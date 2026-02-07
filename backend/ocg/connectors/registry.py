from ocg.connectors.base import Connector
from ocg.connectors.github import GitHubConnector
from ocg.connectors.jira import JiraConnector
from ocg.connectors.slack import SlackConnector


CONNECTOR_REGISTRY: dict[str, Connector] = {
    "slack": SlackConnector(),
    "jira": JiraConnector(),
    "github": GitHubConnector(),
}

