import pytest

from ocg.connectors.github import GitHubConnector
from ocg.connectors.jira import JiraConnector
from ocg.connectors.slack import SlackConnector


@pytest.mark.parametrize("connector", [SlackConnector(), JiraConnector(), GitHubConnector()])
def test_connectors_require_secret_ref(connector):
    with pytest.raises(ValueError):
        connector.validate({"auth": {"token_ref": "plain-token"}, "scopes": ["read:all"]})


@pytest.mark.parametrize("connector", [SlackConnector(), JiraConnector(), GitHubConnector()])
def test_connectors_reject_write_scope(connector):
    with pytest.raises(ValueError):
        connector.validate({"auth": {"token_ref": "env:TOKEN"}, "scopes": ["repo:write"]})

