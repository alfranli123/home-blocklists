#!/usr/bin/env python3
"""Build lists/spamhaus-drop-v4.txt from the Spamhaus DROP list (IPv4).

One CIDR per line, '#' header lines (UniFi Network Lists skip them).
Spamhaus's copyright and timestamp are kept at the top of the file, as
their terms require when redistributing: https://www.spamhaus.org/drop/terms/

Safety: exits non-zero WITHOUT touching the file when the download or parse
fails, when there are fewer than MIN_ENTRIES ranges, or when the list shrinks
by more than MAX_DROP versus the committed file. The file is only rewritten
when the set of ranges changes, so the repo gets a commit only on real changes.
"""
import datetime
import ipaddress
import json
import pathlib
import sys
import urllib.request

SOURCE = "https://www.spamhaus.org/drop/drop_v4.json"
OUT = pathlib.Path(__file__).parent / "lists" / "spamhaus-drop-v4.txt"
MIN_ENTRIES = 500
MAX_DROP = 0.25          # fail if the new list is more than 25% smaller
MIN_PREFIXLEN = 8        # never publish anything broader than a /8


def fail(msg):
    print(f"FAIL: {msg}; {OUT.name} left unchanged", file=sys.stderr)
    sys.exit(1)


def current_ranges():
    if not OUT.exists():
        return []
    return [l.strip() for l in OUT.read_text().splitlines() if l.strip() and not l.startswith("#")]


def main():
    try:
        req = urllib.request.Request(SOURCE, headers={"User-Agent": "home-blocklists-build/1.0"})
        raw = urllib.request.urlopen(req, timeout=60).read().decode()
    except Exception as e:
        fail(f"download error {e!r}")

    nets, meta = [], None
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            fail(f"unparseable line {line[:80]!r}")
        if obj.get("type") == "metadata":
            meta = obj
            continue
        if "cidr" not in obj:
            continue
        try:
            net = ipaddress.ip_network(obj["cidr"], strict=True)
        except ValueError:
            fail(f"invalid CIDR {obj['cidr']!r}")
        if net.version != 4:
            continue
        if not net.is_global:
            print(f"skip non-global {net}", file=sys.stderr)
            continue
        if net.prefixlen < MIN_PREFIXLEN:
            fail(f"suspiciously broad range {net}")
        nets.append(net)

    if meta is None:
        fail("no metadata line (copyright/timestamp) in the source")
    ranges = [str(n) for n in ipaddress.collapse_addresses(nets)]
    if len(ranges) < MIN_ENTRIES:
        fail(f"only {len(ranges)} ranges (minimum {MIN_ENTRIES})")
    old = current_ranges()
    if old and len(ranges) < len(old) * (1 - MAX_DROP):
        fail(f"list shrank from {len(old)} to {len(ranges)} ranges (more than {int(MAX_DROP*100)}%)")
    if ranges == old:
        print(f"unchanged: {len(ranges)} ranges")
        return

    stamp = datetime.datetime.fromtimestamp(meta["timestamp"], datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    header = [
        "# Spamhaus DROP List (IPv4) - data from The Spamhaus Project",
        f"# {meta.get('copyright', '(c) The Spamhaus Project SLU')}",
        f"# Spamhaus list timestamp: {stamp}",
        f"# Source: {SOURCE}",
        f"# Terms: {meta.get('terms', 'https://www.spamhaus.org/drop/terms/')}",
        f"# Ranges: {len(ranges)} (collapsed from {len(nets)} records)",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(header + ranges) + "\n")
    print(f"updated: {len(old)} -> {len(ranges)} ranges")


if __name__ == "__main__":
    main()
