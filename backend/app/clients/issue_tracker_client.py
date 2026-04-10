from __future__ import annotations

from dataclasses import dataclass


class IssueTrackerUnavailableError(RuntimeError):
    pass


@dataclass(slots=True)
class IssueTrackerTicket:
    external_reference: str


@dataclass(slots=True)
class IssueTrackerPayload:
    report_type: str
    description: str
    contact_email: str | None
    submitter_kind: str
    submitter_user_id: str | None
    correlation_id: str | None


class IssueTrackerClient:
    _test_mode = "success"
    _test_records: list[IssueTrackerPayload] = []

    @classmethod
    def reset_for_tests(cls) -> None:
        cls._test_mode = "success"
        cls._test_records = []

    @classmethod
    def set_mode_for_tests(cls, mode: str) -> None:
        cls._test_mode = mode

    @classmethod
    def get_records_for_tests(cls) -> list[IssueTrackerPayload]:
        return list(cls._test_records)

    def submit(self, payload: IssueTrackerPayload) -> IssueTrackerTicket:
        if self._test_mode == "unavailable":
            raise IssueTrackerUnavailableError("Issue tracker is unavailable")
        if self._test_mode == "error":
            raise RuntimeError("Issue tracker rejected the submission")
        self._test_records.append(payload)
        return IssueTrackerTicket(external_reference=f"FB-{len(self._test_records):05d}")
