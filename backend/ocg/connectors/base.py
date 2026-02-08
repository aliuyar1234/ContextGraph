from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


FORBIDDEN_WRITE_SCOPE_MARKERS = ("write", "admin", "delete", "post", "publish", "merge")


@dataclass(frozen=True)
class ConnectorEvent:
    tool: str
    external_event_id: str
    fetched_at: datetime
    payload_json: dict[str, Any]
    permission_state: str


@dataclass(frozen=True)
class NormalizedTrace:
    tool: str
    tool_family: str
    action_type: str
    external_event_id: str
    event_time: datetime
    actor_principal_id: str | None
    resource_ref: tuple[str, str] | None
    related_resource_refs: list[tuple[str, str]]
    entity_tags_json: dict[str, Any]
    metadata_json: dict[str, Any]
    permission_state: str


@dataclass(frozen=True)
class ResourceDelta:
    tool: str
    resource_type: str
    external_id: str
    url: str | None
    title: str | None
    permission_state: str
    acl_principal_ids: list[str]


class Connector(ABC):
    tool: str

    @abstractmethod
    def validate(self, config: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def fetch_events(self, config: dict[str, Any]) -> list[ConnectorEvent]:
        raise NotImplementedError

    @abstractmethod
    def fetch_acls(self, config: dict[str, Any]) -> list[ResourceDelta]:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, event: ConnectorEvent) -> tuple[NormalizedTrace, ResourceDelta | None]:
        raise NotImplementedError

    @staticmethod
    def validate_read_only_scopes(scopes: list[str]) -> None:
        for scope in scopes:
            lower = scope.lower()
            if any(marker in lower for marker in FORBIDDEN_WRITE_SCOPE_MARKERS):
                raise ValueError(f"Rejected non-read-only scope: {scope}")

    @staticmethod
    def now() -> datetime:
        return datetime.now(tz=UTC)
