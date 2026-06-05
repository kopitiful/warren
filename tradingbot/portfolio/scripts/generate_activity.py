import json, os, requests
from datetime import datetime, timedelta, timezone

token = os.environ["GH_PAT"]
username = os.environ.get("GH_USER", "kopitiful")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

now = datetime.now(timezone.utc)
from_date = (now - timedelta(days=365)).isoformat()
to_date = now.isoformat()

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

resp = requests.post(
    "https://api.github.com/graphql",
    headers=headers,
    json={"query": query, "variables": {"login": username, "from": from_date, "to": to_date}},
    timeout=30
)
resp.raise_for_status()
data = resp.json()
if "errors" in data:
    raise RuntimeError(data["errors"])

calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

output = {
    "generated": now.strftime("%Y-%m-%d"),
    "total": calendar["totalContributions"],
    "weeks": [
        {"days": [{"date": d["date"], "count": d["contributionCount"]} for d in w["contributionDays"]]}
        for w in calendar["weeks"]
    ]
}

with open("activity.json", "w") as f:
    json.dump(output, f)

print(f"activity.json: {output['total']} contributions, {len(output['weeks'])} weeks")
