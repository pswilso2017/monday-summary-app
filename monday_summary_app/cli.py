import argparse
import html as html_lib
import os
import pathlib
import sys
import webbrowser
from datetime import datetime, timezone

import requests


_MONDAY_API_URL = "https://api.monday.com/v2"

_BOARD_QUERY = """
query ($boardId: ID!, $maxUpdates: Int!) {
  boards(ids: [$boardId]) {
    name
    groups {
      id
      title
    }
    items_page(limit: 500) {
      items {
        id
        name
        updates(limit: $maxUpdates) {
          id
          body
          created_at
          creator {
            name
          }
        }
      }
    }
  }
}
"""


def get_config(args):
    """Read required settings from CLI args, falling back to environment variables."""
    token = (args.token or os.environ.get("MONDAY_API_TOKEN", "")).strip()
    board_id = (args.board_id or os.environ.get("MONDAY_BOARD_ID", "")).strip()

    missing = []
    if not token:
        missing.append("MONDAY_API_TOKEN  (or pass --token)")
    if not board_id:
        missing.append("MONDAY_BOARD_ID   (or pass --board-id)")

    if missing:
        print(
            "Error: the following required value(s) are not set:\n"
            + "\n".join(f"  {v}" for v in missing)
            + "\n\nProvide them as flags or environment variables, for example:\n"
            "  monday-summary --token YOUR_TOKEN --board-id 1234567890\n"
            "  export MONDAY_API_TOKEN=your_token_here\n"
            "  export MONDAY_BOARD_ID=1234567890",
            file=sys.stderr,
        )
        sys.exit(1)

    return {"token": token, "board_id": board_id}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Print a concise summary of a monday.com board.",
    )
    parser.add_argument(
        "--token",
        default=None,
        metavar="TOKEN",
        help="monday.com personal API token (overrides MONDAY_API_TOKEN env var).",
    )
    parser.add_argument(
        "--board-id",
        default=None,
        dest="board_id",
        metavar="ID",
        help="Numeric board ID to summarise (overrides MONDAY_BOARD_ID env var).",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Write the summary to summary.html in the app directory.",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        dest="open_browser",
        help="Open the generated HTML file in the default browser (requires --html).",
    )
    parser.add_argument(
        "--updates",
        type=int,
        default=10,
        metavar="N",
        help="Number of recent updates to include in the summary (default: 10).",
    )
    return parser.parse_args()


def fetch_board_summary(config, max_updates):
    """Call the monday.com GraphQL API and return a parsed summary dict."""
    headers = {
        "Authorization": config["token"],
        "Content-Type": "application/json",
        "API-Version": "2024-01",
    }
    payload = {
        "query": _BOARD_QUERY,
        "variables": {
            "boardId": config["board_id"],
            "maxUpdates": max_updates,
        },
    }

    response = requests.post(_MONDAY_API_URL, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        messages = "; ".join(e.get("message", str(e)) for e in data["errors"])
        print(f"Error: monday.com API returned errors: {messages}", file=sys.stderr)
        sys.exit(1)

    board = data["data"]["boards"][0]
    groups = [{"id": g["id"], "title": g["title"]} for g in board["groups"]]
    items = board["items_page"]["items"]

    recent_updates = []
    for item in items:
        for update in item.get("updates", []):
            if len(recent_updates) >= max_updates:
                break
            recent_updates.append(
                {
                    "item_name": item["name"],
                    "body": update.get("body", ""),
                    "created_at": update.get("created_at", ""),
                    "creator": (update.get("creator") or {}).get("name", "Unknown"),
                }
            )
        if len(recent_updates) >= max_updates:
            break

    return {
        "board_name": board["name"],
        "group_count": len(groups),
        "groups": groups,
        "item_count": len(items),
        "recent_updates": recent_updates,
    }


def _format_timestamp(iso_str):
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return iso_str


def print_summary(summary):
    sep = "-" * 60
    print(sep)
    print(f"Board:   {summary['board_name']}")
    print(f"Groups:  {summary['group_count']}")
    print(f"Items:   {summary['item_count']}")
    print(sep)

    print("\nGroups")
    for group in summary["groups"]:
        print(f"  • {group['title']}")

    print(f"\nRecent Updates ({len(summary['recent_updates'])})")
    if summary["recent_updates"]:
        for update in summary["recent_updates"]:
            ts = _format_timestamp(update["created_at"])
            print(f"  [{ts}] {update['creator']} on \"{update['item_name']}\"")
            body = update["body"].strip()
            if body:
                for line in body.splitlines():
                    print(f"      {line}")
    else:
        print("  (no updates found)")

    print(sep)


def write_html(summary, path):
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def esc(text):
        return html_lib.escape(str(text))

    group_rows = "\n".join(
        f"        <tr><td>{esc(group['title'])}</td></tr>" for group in summary["groups"]
    )

    if summary["recent_updates"]:
        update_items_html = ""
        for update in summary["recent_updates"]:
            ts = esc(_format_timestamp(update["created_at"]))
            creator = esc(update["creator"])
            item_name = esc(update["item_name"])
            body = esc(update["body"].strip()) if update["body"] else ""
            body_html = f"<div>{body}</div>" if body else ""
            update_items_html += (
                f'    <div class="update-item">\n'
                f'      {body_html}\n'
                f'      <div class="update-meta">{ts} &nbsp;|&nbsp; '
                f'{creator} on <strong>{item_name}</strong></div>\n'
                f'    </div>\n'
            )
    else:
        update_items_html = "    <p>No updates found.</p>\n"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Monday Board Summary — {esc(summary['board_name'])}</title>
  <style>
    body {{
      font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
      font-size: 15px;
      line-height: 1.6;
      color: #1f2328;
      background: #ffffff;
      margin: 0;
      padding: 2rem 1rem;
    }}
    .container {{
      max-width: 760px;
      margin: 0 auto;
    }}
    h1 {{
      font-size: 1.4rem;
      margin-bottom: 0.25rem;
    }}
    .meta {{
      color: #57606a;
      font-size: 0.85rem;
      margin-bottom: 1.5rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 1.5rem;
    }}
    th {{
      text-align: left;
      padding: 0.4rem 0.6rem;
      background: #f7f8fa;
      border: 1px solid #e5e7eb;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #57606a;
    }}
    td {{
      padding: 0.4rem 0.6rem;
      border: 1px solid #e5e7eb;
      vertical-align: top;
    }}
    tr:nth-child(even) td {{
      background: #f7f8fa;
    }}
    h2 {{
      font-size: 1rem;
      margin-bottom: 0.5rem;
      border-bottom: 1px solid #e5e7eb;
      padding-bottom: 0.25rem;
    }}
    .update-item {{
      padding: 0.4rem 0;
      border-bottom: 1px solid #e5e7eb;
      font-size: 0.9rem;
    }}
    .update-item:last-child {{
      border-bottom: none;
    }}
    .update-meta {{
      font-size: 0.78rem;
      color: #57606a;
    }}
    footer {{
      margin-top: 2rem;
      padding-top: 1rem;
      border-top: 1px solid #e5e7eb;
      text-align: center;
      font-size: 0.75rem;
      color: #57606a;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{esc(summary['board_name'])}</h1>
    <p class="meta">Generated: {esc(generated)}</p>
    <h2>Board Overview</h2>
    <table>
      <thead>
        <tr><th>Metric</th><th>Value</th></tr>
      </thead>
      <tbody>
        <tr><td>Total Groups</td><td>{summary['group_count']}</td></tr>
        <tr><td>Total Items</td><td>{summary['item_count']}</td></tr>
      </tbody>
    </table>
    <h2>Groups</h2>
    <table>
      <thead>
        <tr><th>Group Name</th></tr>
      </thead>
      <tbody>
{group_rows}
      </tbody>
    </table>
    <h2>Recent Updates ({len(summary['recent_updates'])})</h2>
{update_items_html}
    <footer>Generated by monday_summary_app on {esc(generated)}</footer>
  </div>
</body>
</html>
"""

    path.write_text(html_content, encoding="utf-8")
    print(f"HTML summary written to: {path.resolve()}")


def open_in_browser(path):
    url = path.resolve().as_uri()
    webbrowser.open(url)
    print(f"Opened in browser: {url}")


def main():
    args = parse_args()
    config = get_config(args)
    app_dir = pathlib.Path(__file__).resolve().parent.parent
    html_path = app_dir / "summary.html"

    summary = fetch_board_summary(config, max_updates=args.updates)
    print_summary(summary)

    if args.html:
        write_html(summary, path=html_path)
        if args.open_browser:
            open_in_browser(path=html_path)

    return 0
