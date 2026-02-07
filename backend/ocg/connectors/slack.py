from datetime import UTC, datetime
from typing import Any

from ocg.connectors.base import Connector, ConnectorEvent, NormalizedTrace, ResourceDelta


class SlackConnector(Connector):
    tool = "slack"

    def validate(self, config: dict[str, Any]) -> None:
        scopes = list(config.get("scopes", ["channels:read", "groups:read", "users:read"]))
        self.validate_read_only_scopes(scopes)
        token_ref = str(config.get("auth", {}).get("token_ref", ""))
        if not token_ref.startswith("env:"):
            raise ValueError("Slack token must be a secret reference (env:...).")

    def fetch_events(self, config: dict[str, Any]) -> list[ConnectorEvent]:
        now = self.now()
        payload = {
            "event_type": "message_metadata",
            "channel_id": "C-DEMO",
            "actor": "demo-user",
            "message_body_stored": False,
            "ts": now.isoformat(),
        }
        return [
            ConnectorEvent(
                tool=self.tool,
                external_event_id=f"slack-{int(now.timestamp())}",
                fetched_at=now,
                payload_json=payload,
                permission_state="KNOWN",
            )
        ]

    def fetch_acls(self, config: dict[str, Any]) -> list[ResourceDelta]:
        return [
            ResourceDelta(
                tool=self.tool,
                resource_type="channel",
                external_id="C-DEMO",
                url=None,
                title="",
                permission_state="KNOWN",
                acl_principal_ids=["group:analyst", "group:admin", "demo-user"],
            )
        ]

    def normalize(self, event: ConnectorEvent) -> tuple[NormalizedTrace, ResourceDelta | None]:
        ts = datetime.fromisoformat(event.payload_json["ts"]).astimezone(UTC)
        trace = NormalizedTrace(
            tool=self.tool,
            tool_family="chat",
            action_type="message",
            external_event_id=event.external_event_id,
            event_time=ts,
            actor_principal_id=event.payload_json.get("actor"),
            resource_ref=("channel", event.payload_json["channel_id"]),
            related_resource_refs=[],
            entity_tags_json={"entity_type_tags": ["Channel"]},
            metadata_json={"event_type": event.payload_json["event_type"], "raw_content": False},
            permission_state=event.permission_state,
        )
        delta = ResourceDelta(
            tool=self.tool,
            resource_type="channel",
            external_id=event.payload_json["channel_id"],
            url=None,
            title="",
            permission_state=event.permission_state,
            acl_principal_ids=["group:analyst", "group:admin", "demo-user"],
        )
        return trace, delta
