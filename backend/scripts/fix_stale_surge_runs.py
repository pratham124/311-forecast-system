from __future__ import annotations

import argparse

from sqlalchemy import select

from app.core.db import get_session_factory, run_migrations
from app.models import SurgeEvaluationRun


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mark stale running surge evaluation rows as completed_with_failures.",
    )
    parser.add_argument(
        "--reason",
        default="Marked stale after pipeline failure hardening.",
        help="Failure summary to apply when an existing failure summary is empty.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print affected rows without updating them.",
    )
    args = parser.parse_args()

    run_migrations()
    session = get_session_factory()()
    try:
        rows = list(
            session.scalars(
                select(SurgeEvaluationRun).where(SurgeEvaluationRun.status == "running").order_by(SurgeEvaluationRun.started_at.asc())
            )
        )
        if not rows:
            print("No stale running surge evaluation rows found.")
            return 0

        print(f"Found {len(rows)} stale running surge evaluation row(s).")
        for row in rows:
            print(
                f"- surge_evaluation_run_id={row.surge_evaluation_run_id} "
                f"ingestion_run_id={row.ingestion_run_id} "
                f"started_at={row.started_at.isoformat() if row.started_at else 'unknown'}"
            )

        if args.dry_run:
            print("Dry run only. No changes written.")
            session.rollback()
            return 0

        for row in rows:
            row.status = "completed_with_failures"
            row.failure_summary = row.failure_summary or args.reason
            row.completed_at = row.completed_at or row.started_at
        session.commit()
        print("Updated stale running surge evaluation rows.")
        return 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
