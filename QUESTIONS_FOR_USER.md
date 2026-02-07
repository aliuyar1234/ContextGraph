# Questions for user (non-blocking unless explicitly marked)

## Q-0001 (NON-BLOCKING): Which process domain should dashboards optimize for first?
Baseline chosen: incident response (engineering/SRE) because Slack+Jira+GitHub yields strong signal coverage.
- If you prefer sales/onboarding, the process_key derivation and connector priorities shift.

## Q-0002 (NON-BLOCKING): Do you want Confluence/Notion in MVP?
Baseline chosen: ship after MVP; keep MVP to Slack/Jira/GitHub to reduce connector surface.

## Q-0003 (NON-BLOCKING): Should aggregated analytics be visible to all users or only `analyst/admin`?
Baseline chosen: `analyst/admin` by default; optionally allow org-wide viewing via config.
Reason: reduces privacy perception risk and aligns with “no surveillance”.

## Q-0004 (NON-BLOCKING): Do you want a built-in “demo dataset generator” for impressive screenshots?
Baseline chosen: yes (`ocg seed demo`) to power dashboards without real integrations.

## Q-0005 (NON-BLOCKING): Preferred OSS license if not Apache-2.0?
Baseline chosen: Apache-2.0 per PROJECT_LOCK; change only via CHANGE_REQUEST.
