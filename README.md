# home-blocklists

Plain-text IP block lists for a home UniFi network, rebuilt daily by a GitHub Action.

| File | Contents | Raw URL |
|---|---|---|
| `lists/spamhaus-drop-v4.txt` | Spamhaus DROP (IPv4), one CIDR per line | https://raw.githubusercontent.com/alfranli123/home-blocklists/main/lists/spamhaus-drop-v4.txt |

## Source and credit
The data is the **Spamhaus DROP List**, (c) The Spamhaus Project SLU, provided free of charge under the
[DROP terms](https://www.spamhaus.org/drop/terms/). Spamhaus's copyright and the list timestamp are kept
at the top of each file, as the terms require. eDROP was merged into DROP on 10 April 2024, so DROP alone
covers both.

## How it is built
`build.py` downloads `drop_v4.json`, keeps valid global IPv4 ranges (nothing broader than /8), collapses
them and writes the file. The Action (`.github/workflows/build.yml`) runs daily and on demand, and commits
only when the list changes. A failed download, fewer than 500 ranges, or a drop of more than 25% versus the
committed list fails the run without touching the file, so the last good list stays published.
