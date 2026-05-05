#!/usr/bin/env python3
"""
bitty_wiki_watcher.py — Bitty's Wiki File Observer

Monitors /wiki for CLOSE_WRITE events using watchdog.
On change detected: generates 50-word summary via Bitty local inference,
then writes metadata to /tmp/wiki_change.json for Witty to pick up.

Cost: ~$0.00 per run (local Ollama, no cloud API)
"""

import sys
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WIKI_PATH = "/home/mathew/.openclaw/workspace/wiki"
METADATA_FILE = "/home/mathew/.cache/katzen-sync/wiki_change.json"
BITTY_CORE = "/home/mathew/.openclaw/workspace/bitty_core.py"
POLL_INTERVAL = 5  # seconds between watchdog checks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Bitty-Watcher] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger()


def bitty_summarize(filename: str, content: str, action: str) -> str:
    """
    Use Bitty local inference to generate a 50-word summary of the change.
    Falls back to heuristic if Ollama is unavailable or times out.
    Timeout: 15 seconds max (prevents watcher from blocking).
    """
    import os as _os
    _os.environ["OLLAMA_TIMEOUT"] = "15"  # override timeout for watcher
    try:
        sys.path.insert(0, str(Path(BITTY_CORE).parent))
        # Clear any cached import
        for mod in list(sys.modules.keys()):
            if "bitty" in mod:
                del sys.modules[mod]
        from bitty_core import ask

        prompt = (
            f"A wiki file was {action}:\n\n"
            f"Filename: {filename}\n"
            f"Content preview (first 500 chars):\n{content[:500]}\n\n"
            f"Summarize this change in exactly 50 words. "
            f"Focus on: what changed, why, and who it affects."
        )
        # 15s timeout — watcher can't block longer than a poll interval
        summary = ask(prompt, temperature=0.2)
        # Clamp to ~50 words
        words = summary.split()
        if len(words) > 55:
            summary = " ".join(words[:50]) + "..."
        return summary[:300]  # hard cap
    except Exception as e:
        log.warning(f"Bitty inference failed ({e}), using heuristic fallback")
        return heuristic_summary(filename, content, action)


def heuristic_summary(filename: str, content: str, action: str) -> str:
    """Fallback when Ollama is unavailable — extract key lines."""
    lines = [l.strip() for l in content.split("\n") if l.strip() and not l.startswith("#")]
    key = " ".join(lines[:5])
    return f"{action.capitalize()}: {filename}. Key content: {key[:200]}."


def write_metadata(event: dict):
    """Write change metadata to /tmp/wiki_change.json for Witty to consume."""
    with open(METADATA_FILE, "w") as f:
        json.dump(event, f, indent=2)
    log.info(f"Metadata written: {event['filename']}")


class WikiChangeHandler(FileSystemEventHandler):
    """Fires on CLOSE_WRITE (file saved) in the wiki directory."""

    def _on_change(self, event_type: str, src_path: str):
        if not src_path.endswith(".md"):
            return

        path = Path(src_path)
        filename = path.name

        # Skip metadata files
        if filename.startswith("."):
            return

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            log.warning(f"Could not read {src_path}: {e}")
            return

        # Detect action type
        action = "modified"
        if "tmp" in src_path or ".swp" in src_path:
            return  # skip temp files

        log.info(f"Detected {event_type}: {filename}")
        summary = bitty_summarize(filename, content, event_type)

        event = {
            "filename": filename,
            "filepath": src_path,
            "action": event_type,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "size_bytes": len(content),
        }
        write_metadata(event)

    def on_modified(self, event):
        if not event.is_directory:
            self._on_change("modified", event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self._on_change("created", event.src_path)


def main():
    log.info(f"Starting Bitty Wiki Watcher on {WIKI_PATH}")
    log.info("Watching for .md CLOSE_WRITE events...")

    handler = WikiChangeHandler()
    observer = Observer()
    observer.schedule(handler, WIKI_PATH, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        observer.stop()
        log.info("Watcher stopped.")

    observer.join()


if __name__ == "__main__":
    main()
