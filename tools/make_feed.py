#!/usr/bin/env python3
"""Regenerate feed.xml from feed_config.json + episodes.json.

Run from anywhere; paths resolve relative to the repo root. Audio files
must exist in audio/ — a manifest entry whose file is missing fails the
build rather than shipping a dead enclosure.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent

MIME = {".mp3": "audio/mpeg", ".m4a": "audio/x-m4a"}


def duration_seconds(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True)
    return int(float(out.stdout.strip()))


def hms(seconds):
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def rfc2822(iso):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return format_datetime(dt)


def main():
    cfg = json.loads((ROOT / "feed_config.json").read_text())
    episodes = json.loads((ROOT / "episodes.json").read_text())
    base = cfg["base_url"].rstrip("/")

    items = []
    for ep in sorted(episodes, key=lambda e: e["pubDate"], reverse=True):
        if ep.get("draft"):
            continue
        audio = ROOT / "audio" / ep["file"]
        if not audio.exists():
            sys.exit(f"missing audio file: {audio}")
        mime = MIME.get(audio.suffix)
        if not mime:
            sys.exit(f"unsupported audio type: {audio}")
        art = ""
        if ep.get("art") and (ROOT / "art" / ep["art"]).exists():
            art = f'\n      <itunes:image href="{base}/art/{ep["art"]}"/>'
        if ep.get("season") is not None:
            art += f'\n      <itunes:season>{ep["season"]}</itunes:season>'
        if ep.get("episode") is not None:
            art += f'\n      <itunes:episode>{ep["episode"]}</itunes:episode>'
        items.append(f"""    <item>
      <title>{escape(ep["title"])}</title>
      <guid isPermaLink="false">{escape(ep["guid"])}</guid>
      <pubDate>{rfc2822(ep["pubDate"])}</pubDate>
      <description><![CDATA[{ep["description"]}]]></description>
      <enclosure url="{base}/audio/{ep["file"]}" length="{audio.stat().st_size}" type="{mime}"/>
      <itunes:duration>{hms(duration_seconds(audio))}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>{art}
    </item>""")

    # Apple Podcasts Connect show-claim token; harmless to keep after the claim completes.
    claim = ""
    if cfg.get("apple_claim_token"):
        claim = (f'\n    <podcast:txt purpose="applepodcastsverify">'
                 f'{cfg["apple_claim_token"]}</podcast:txt>')

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:podcast="https://podcastindex.org/namespace/1.0">
  <channel>
    <title>{escape(cfg["title"])}</title>
    <link>{escape(cfg["link"])}</link>
    <atom:link href="{base}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>{escape(cfg["description"])}</description>
    <language>{cfg["language"]}</language>
    <lastBuildDate>{format_datetime(datetime.now(timezone.utc))}</lastBuildDate>
    <itunes:author>{escape(cfg["author"])}</itunes:author>
    <itunes:owner>
      <itunes:name>{escape(cfg["author"])}</itunes:name>
      <itunes:email>{cfg["email"]}</itunes:email>
    </itunes:owner>
    <itunes:image href="{base}/{cfg["cover"]}"/>
    <itunes:category text="{cfg["category"]}"/>
    <itunes:explicit>false</itunes:explicit>{claim}
{chr(10).join(items)}
  </channel>
</rss>
"""
    (ROOT / "feed.xml").write_text(feed)
    print(f"feed.xml written: {len(items)} episodes")


if __name__ == "__main__":
    main()
