from datetime import UTC, datetime
from typing import Any

from ocg.connectors.base import Connector, ConnectorEvent, NormalizedTrace, ResourceDelta


class GitHubConnector(Connector):
    tool = "github"

    def validate(self, config: dict[str, Any]) -> None:
        scopes = list(config.get("scopes", ["read:org", "repo:status", "read:user"]))
        self.validate_read_only_scopes(scopes)
        token_ref = str(config.get("auth", {}).get("token_ref", ""))
        if not token_ref.startswith("env:"):
            raise ValueError("GitHub token must be a secret reference (env:...).")

    def fetch_events(self, config: dict[str, Any]) -> list[ConnectorEvent]:
        now = self.now()
        return [
            ConnectorEvent(
                tool=self.tool,
                external_event_id=f"github-{int(now.timestamp())}",
                fetched_at=now,
                payload_json={
                    "repo": "acme/context-graph",
                    "pr": 42,
                    "action": "opened",
                    "actor": "demo-user",
                    "ts": now.isoformat(),
                },
                permission_state="KNOWN",
            )
        ]

    def fetch_acls(self, config: dict[str, Any]) -> list[ResourceDelta]:
        return [
            ResourceDelta(
                tool=self.tool,
                resource_type="repository",
                external_id="acme/context-graph",
                url="https://github.com/acme/context-graph",
                title="",
                permission_state="KNOWN",
                acl_principal_ids=["group:analyst", "group:admin", "demo-user"],
            )
        ]

    def normalize(self, event: ConnectorEvent) -> tuple[NormalizedTrace, ResourceDelta | None]:
        ts = datetime.fromisoformat(event.payload_json["ts"]).astimezone(UTC)
        trace = NormalizedTrace(
            tool=self.tool,
            tool_family="code",
            action_type="create",
            external_event_id=event.external_event_id,
            event_time=ts,
            actor_principal_id=event.payload_json.get("actor"),
            resource_ref=("repository", event.payload_json["repo"]),
            related_resource_refs=[],
            entity_tags_json={"entity_type_tags": ["Repository"], "service": "context-graph"},
            metadata_json={"pr": event.payload_json["pr"], "action": event.payload_json["action"]},
            permission_state=event.permission_state,
        )
        delta = ResourceDelta(
            tool=self.tool,
            resource_type="repository",
            external_id=event.payload_json["repo"],
            url="https://github.com/acme/context-graph",
            title="",
            permission_state=event.permission_state,
            acl_principal_ids=["group:analyst", "group:admin", "demo-user"],
        )
        return trace, delta
