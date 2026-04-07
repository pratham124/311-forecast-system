from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


GuideStatus = Literal["available", "unavailable", "error"]
GuideOutcome = Literal["retrieved", "retrieval_failed", "rendered", "render_failed"]
GuideFailureCategory = Literal["guide_unavailable", "guide_render_failed"]


class GuideSection(BaseModel):
    section_id: str = Field(alias="sectionId")
    label: str
    order_index: int = Field(alias="orderIndex", ge=0)
    anchor_target: str | None = Field(default=None, alias="anchorTarget")
    content_excerpt: str | None = Field(default=None, alias="contentExcerpt")

    model_config = ConfigDict(populate_by_name=True)


class UserGuideView(BaseModel):
    guide_access_event_id: str = Field(alias="guideAccessEventId")
    status: GuideStatus
    title: str | None = None
    published_at: datetime | None = Field(default=None, alias="publishedAt")
    body: str | None = None
    sections: list[GuideSection] | None = None
    status_message: str | None = Field(default=None, alias="statusMessage")
    entry_point: str = Field(alias="entryPoint")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_status_fields(self):
        if self.status == "available":
            if not self.title or self.published_at is None or self.body is None or self.sections is None:
                raise ValueError("available guide views require title, publishedAt, body, and sections")
        elif not self.status_message:
            raise ValueError("unavailable and error guide views require statusMessage")
        return self


class GuideRenderOutcomeRequest(BaseModel):
    render_outcome: Literal["rendered", "render_failed"] = Field(alias="renderOutcome")
    failure_message: str | None = Field(default=None, alias="failureMessage")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_failure_message(self):
        if self.render_outcome == "render_failed" and not self.failure_message:
            raise ValueError("failureMessage is required when renderOutcome is render_failed")
        return self


class GuideSourceDocument(BaseModel):
    guide_content_id: str
    title: str
    published_at: datetime
    body: str
    sections: list[GuideSection]
