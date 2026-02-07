from ocg.connectors.slack import SlackConnector


def test_slack_metadata_only_default():
    connector = SlackConnector()
    event = connector.fetch_events({"auth": {"token_ref": "env:SLACK_TOKEN"}})[0]
    assert event.payload_json.get("message_body_stored") is False

