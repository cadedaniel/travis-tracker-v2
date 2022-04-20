import os
import sqlite3
import requests
from dotenv import load_dotenv
import sys

load_dotenv()

db = sqlite3.connect("./results.db")
top_failed_tests = list(
    db.execute(
        """
SELECT
  test_name,
  MIN(commits.idx) as most_recent_failure,
  COUNT(*) as failed_count
FROM test_result, commits
WHERE test_result.sha == commits.sha
  AND status == 'FAILED'
  AND commits.idx < 20
GROUP BY test_name
  HAVING COUNT(*) >= 5
ORDER BY failed_count DESC;
"""
    )
)

has_flaky_tests = False
markdown_lines = ["🚓 Your Flaky Test Report of the Day (posted 9AM each weekday)"]
for name, most_recent, count in top_failed_tests:
    if most_recent > 2:
        # Most recent 3 runs have been successful. Test may have been fixed.
        continue
    has_flaky_tests = True
    markdown_lines.append(f"- `{name}` failed *{count}* times over latest 20 tests.")
markdown_lines.append("Go to https://flakey-tests.ray.io/ to view Travis links")

if not has_flaky_tests:
    print("No failed cases, skipping.")
    sys.exit(0)

slack_url = os.environ["SLACK_WEBHOOK"]
slack_channnel = os.environ.get("SLACK_CHANNEL_OVERRIDE", "#open-source")

resp = requests.post(
    slack_url,
    json={
        "text": "\n".join(markdown_lines),
        "channel": slack_channnel,
        "username": "Flaky Bot",
        "icon_emoji": ":snowflake:",
    },
)
print(resp.status_code)
print(resp.text)
