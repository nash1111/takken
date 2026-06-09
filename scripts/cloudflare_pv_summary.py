#!/usr/bin/env python3
"""Summarize takkensokuto.com Cloudflare Web Analytics/RUM PV.

The script prints Markdown suitable for GitHub Actions job summaries.
It never prints tokens. Configure with environment variables:

- CLOUDFLARE_API_TOKEN: API token with account analytics read access
- CLOUDFLARE_ACCOUNT_ID: Cloudflare account id
- TAKKEN_ANALYTICS_HOST: optional, defaults to takkensokuto.com
- TAKKEN_ANALYTICS_TZ: optional, defaults to Asia/Tokyo
- TAKKEN_ANALYTICS_DAYS: optional, defaults to 1
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from zoneinfo import ZoneInfo

GRAPHQL_URL = "https://api.cloudflare.com/client/v4/graphql"


def die(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def graphql(query: str, variables: dict) -> dict:
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token:
        die("CLOUDFLARE_API_TOKEN is required")

    request = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload: dict = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:800]
        die(f"Cloudflare API HTTP {exc.code}: {body}")

    if payload.get("errors"):
        die("Cloudflare GraphQL errors: " + json.dumps(payload["errors"], ensure_ascii=False))
    return payload["data"]


def period(days: int, tz_name: str) -> tuple[dt.datetime, dt.datetime, dt.datetime, dt.datetime]:
    tz = ZoneInfo(tz_name)
    now_local = dt.datetime.now(tz).replace(microsecond=0)
    start_local = now_local.replace(hour=0, minute=0, second=0) - dt.timedelta(days=days - 1)
    return (
        start_local,
        now_local,
        start_local.astimezone(dt.timezone.utc),
        now_local.astimezone(dt.timezone.utc),
    )


def fetch_dimension(account_id: str, host: str, start_utc: dt.datetime, end_utc: dt.datetime, dimension: str, country: str | None = None) -> list[dict]:
    country_filter = ",countryName:$country" if country else ""
    query = f"""
    query($accountTag:String!,$start:Time!,$end:Time!,$host:String!{',$country:String!' if country else ''}) {{
      viewer {{
        accounts(filter:{{accountTag:$accountTag}}) {{
          rumPageloadEventsAdaptiveGroups(
            limit:25,
            filter:{{datetime_geq:$start,datetime_leq:$end,requestHost:$host{country_filter}}},
            orderBy:[count_DESC]
          ) {{
            dimensions {{ {dimension} }}
            count
            sum {{ visits }}
            avg {{ sampleInterval }}
          }}
        }}
      }}
    }}
    """
    variables = {
        "accountTag": account_id,
        "start": start_utc.isoformat().replace("+00:00", "Z"),
        "end": end_utc.isoformat().replace("+00:00", "Z"),
        "host": host,
    }
    if country:
        variables["country"] = country
    data = graphql(query, variables)
    return data["viewer"]["accounts"][0]["rumPageloadEventsAdaptiveGroups"]


def rows_to_table(rows: list[dict], key: str, limit: int = 10) -> str:
    if not rows:
        return "_No data_\n"
    lines = ["| Rank | Value | PV | Visits | Sample |", "| ---: | --- | ---: | ---: | ---: |"]
    for i, row in enumerate(rows[:limit], 1):
        value = row.get("dimensions", {}).get(key) or "(none)"
        visits = (row.get("sum") or {}).get("visits") or 0
        sample = (row.get("avg") or {}).get("sampleInterval") or 1
        lines.append(f"| {i} | `{value}` | {row.get('count', 0)} | {visits} | {sample} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not account_id:
        die("CLOUDFLARE_ACCOUNT_ID is required")
    assert account_id is not None

    host = os.environ.get("TAKKEN_ANALYTICS_HOST", "takkensokuto.com")
    tz_name = os.environ.get("TAKKEN_ANALYTICS_TZ", "Asia/Tokyo")
    days = int(os.environ.get("TAKKEN_ANALYTICS_DAYS", "1"))
    if days < 1:
        die("TAKKEN_ANALYTICS_DAYS must be >= 1")

    start_local, end_local, start_utc, end_utc = period(days, tz_name)
    by_country = fetch_dimension(account_id, host, start_utc, end_utc, "countryName")
    jp_paths = fetch_dimension(account_id, host, start_utc, end_utc, "requestPath", country="JP")
    jp_referrers = fetch_dimension(account_id, host, start_utc, end_utc, "refererHost", country="JP")
    jp_devices = fetch_dimension(account_id, host, start_utc, end_utc, "deviceType", country="JP")

    country_counts = defaultdict(int)
    for row in by_country:
        country_counts[row.get("dimensions", {}).get("countryName") or "(none)"] += row.get("count", 0)

    total_pv = sum(country_counts.values())
    jp_pv = country_counts.get("JP", 0) + country_counts.get("Japan", 0)

    summary = [
        f"# takkensokuto.com PV summary",
        "",
        f"- Period: `{start_local.isoformat()}` → `{end_local.isoformat()}` ({tz_name})",
        f"- Metric: Cloudflare Web Analytics / RUM pageload events (`count`)",
        f"- Total RUM PV: **{total_pv}**",
        f"- Japan RUM PV: **{jp_pv}**",
        "",
        "## Country breakdown",
        rows_to_table(by_country, "countryName"),
        "## Japan top paths",
        rows_to_table(jp_paths, "requestPath"),
        "## Japan referrers",
        rows_to_table(jp_referrers, "refererHost"),
        "## Japan devices",
        rows_to_table(jp_devices, "deviceType"),
    ]
    print("\n".join(summary))


if __name__ == "__main__":
    main()
