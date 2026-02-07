from datetime import UTC, datetime
from typing import Any

from ocg.connectors.base import Connector, ConnectorEvent, NormalizedTrace, ResourceDelta


class JiraConnector(Connector):
    tool = "jira"

    def validate(self, config: dict[str, Any]) -> None:
        scopes = list(config.get("scopes", ["read:jira-work", "read:jira-user"]))
        self.validate_read_only_scopes(scopes)
        token_ref = str(config.get("auth", {}).get("token_ref", ""))
        if not token_ref.startswith("env:"):
            raise ValueError("Jira token must be a secret reference (env:...).")

    def fetch_events(self, config: dict[str, Any]) -> list[ConnectorEvent]:
        now = self.now()
        return [
            ConnectorEvent(
                tool=self.tool,
                external_event_id=f"jira-{int(now.timestamp())}",
                fetched_at=now,
                payload_json={
                    "issue_key": "ENG-123",
                    "actor": "demo-user",
                    "transition": "In Progress",
                    "comment_body_stored": False,
                    "ts": now.isoformat(),
                },
                permission_state="KNOWN",
            )
        ]

    def fetch_acls(self, config: dict[str, Any]) -> list[ResourceDelta]:
        return [
            ResourceDelta(
                tool=self.tool,
                resource_type="ticket",
                external_id="ENG-123",
                url="https://jira.example.com/browse/ENG-123",
                title="",
                permission_state="KNOWN",
                acl_principal_ids=["group:analyst", "group:admin", "demo-user"],
            )
        ]

    def normalize(self, event: ConnectorEvent) -> tuple[NormalizedTrace, ResourceDelta | None]:
        ts = datetime.fromisoformat(event.payload_json["ts"]).astimezone(UTC)
        trace = NormalizedTrace(
            tool=self.tool,
            tool_family="tickets",
            action_type="status_change",
            external_event_id=event.external_event_id,
            event_time=ts,
            actor_principal_id=event.payload_json.get("actor"),
            resource_ref=("ticket", event.payload_json["issue_key"]),
            related_resource_refs=[],
            entity_tags_json={"entity_type_tags": ["Ticket"], "project": "ENG"},
            metadata_json={"transition": event.payload_json["transition"], "raw_content": False},
            permission_state=event.permission_state,
        )
        delta = ResourceDelta(
            tool=self.tool,
            resource_type="ticket",
            external_id=event.payload_json["issue_key"],
            url="https://jira.example.com/browse/ENG-123",
            title="",
            permission_state=event.permission_state,
            acl_principal_ids=["group:analyst", "group:admin", "demo-user"],
        )
        return trace, delta
