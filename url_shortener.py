# URL Shortener & Tracker
# Shorten URLs using TinyURL's free API, store all your links locally
# in SQLite with timestamps, and view your full history in a Rich table.
# A mini URL manager that lives entirely on your machine.
#
# Install: pip install requests rich
# Usage:   python url_shortener.py shorten https://example.com
#          python url_shortener.py shorten https://example.com --note "my blog"
#          python url_shortener.py history

import sqlite3
import requests
import argparse
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()
DB = "urls.db"

def init_db():
    # Set up the SQLite database and create the table if it doesn't exist
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                original    TEXT NOT NULL,
                short       TEXT NOT NULL,
                created_at  TEXT,
                note        TEXT DEFAULT ''
            )
        """)

def shorten_url(long_url):
    # TinyURL offers a free API endpoint — no account or key needed
    api = f"http://tinyurl.com/api-create.php?url={long_url}"
    r = requests.get(api, timeout=8)
    r.raise_for_status()
    return r.text.strip()

def save_url(original, short, note=""):
    # Save the original + shortened URL pair into the database
    with sqlite3.connect(DB) as conn:
        conn.execute(
            "INSERT INTO urls (original, short, created_at, note) VALUES (?,?,?,?)",
            (original, short, datetime.now().strftime("%Y-%m-%d %H:%M"), note)
        )

def show_history():
    # Pull all saved URLs and display them in a Rich table
    with sqlite3.connect(DB) as conn:
        rows = conn.execute(
            "SELECT id, short, original, created_at, note FROM urls ORDER BY id DESC"
        ).fetchall()
    if not rows:
        console.print("[dim]No URLs saved yet.[/dim]")
        return
    table = Table(box=box.SIMPLE_HEAD)
    table.add_column("ID", width=4, style="dim")
    table.add_column("Short URL", width=28)
    table.add_column("Original", min_width=30)
    table.add_column("Created", width=16, style="dim")
    table.add_column("Note", width=16, style="dim")
    for row in rows:
        original = row[2][:45] + "..." if len(row[2]) > 45 else row[2]
        table.add_row(str(row[0]), f"[blue]{row[1]}[/blue]", original, row[3], row[4])
    console.print(table)

def main():
    init_db()
    parser = argparse.ArgumentParser(description="URL Shortener & Tracker")
    sub = parser.add_subparsers(dest="cmd")

    sh = sub.add_parser("shorten", help="Shorten a URL")
    sh.add_argument("url", help="URL to shorten")
    sh.add_argument("--note", default="", help="Optional label for this URL")

    sub.add_parser("history", help="View all saved URLs")
    args = parser.parse_args()

    if args.cmd == "shorten":
        console.print("[dim]Shortening...[/dim]")
        short = shorten_url(args.url)
        save_url(args.url, short, args.note)
        console.print(f"\n[green]Done![/green] [bold]{short}[/bold]")
    elif args.cmd == "history":
        show_history()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
