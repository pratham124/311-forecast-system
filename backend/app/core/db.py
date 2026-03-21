from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


UC01_TABLES = {
    "ingestion_runs",
    "successful_pull_cursors",
    "candidate_datasets",
    "dataset_versions",
    "dataset_records",
    "current_dataset_markers",
    "failure_notification_records",
}

UC02_TABLES = {
    "validation_runs",
    "validation_results",
    "duplicate_analysis_results",
    "duplicate_groups",
    "review_needed_records",
}


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
        _engine = create_engine(settings.database_url, future=True, connect_args=connect_args)
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _session_factory


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def _reconcile_legacy_migration_state(alembic_config: Config) -> None:
    inspector = inspect(get_engine())
    table_names = set(inspector.get_table_names())
    if "alembic_version" in table_names:
        return
    if not UC01_TABLES.issubset(table_names):
        return

    dataset_version_columns = {column["name"] for column in inspector.get_columns("dataset_versions")}
    has_uc02_columns = {"source_dataset_version_id", "dataset_kind", "duplicate_group_count", "approved_by_validation_run_id"}.issubset(
        dataset_version_columns
    )
    has_uc02_tables = UC02_TABLES.issubset(table_names)

    revision = "002_uc02_validation_pipeline" if has_uc02_columns and has_uc02_tables else "001_uc01_ingestion_foundation"
    command.stamp(alembic_config, revision)


def run_migrations() -> None:
    base_dir = Path(__file__).resolve().parents[2]
    alembic_config = Config(str(base_dir / 'alembic.ini'))
    alembic_config.set_main_option('script_location', str(base_dir / 'migrations'))
    alembic_config.set_main_option('sqlalchemy.url', get_settings().database_url)
    _reconcile_legacy_migration_state(alembic_config)
    command.upgrade(alembic_config, 'head')
