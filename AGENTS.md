# AGENTS.md — ormaos-examples

## What this repository is

Example programs for Ormaos, and the hackathon demo page (GitHub Pages, in `docs/`). Public, Apache 2.0. Ormaos itself lives in the sibling repository `ormaos-python`; install it with `pip install -e ../ormaos-python`.

## The demo app: `order-sync/`

A scheduled Python job that syncs orders from a sales system into an inventory.

- **Input:** orders from a local CSV, or a fake local HTTP API (standard library `http.server`, started by the script).
- **Output:** stock levels in a local SQLite database.
- **The bug, on purpose:** a `try/except Exception: log.warning(...); continue` swallows a SKU format error (for example a lowercase or padded SKU) in some orders. The job prints "sync finished: OK" and exits 0, and the inventory is wrong for those SKUs.
- **Realistic, small:** 4 to 6 modules (`fetch`, `parse`, `validate`, `inventory`, `job`), about 450 lines, with a README that describes it as a normal job, not as a bug.
- A `reset.sh` that rebuilds the database and the input, so every run starts the same.
- Other code paths that also change stock and are correct: the guard against an order applied twice, back-orders, pack units. Nothing in `order-sync/` says where the bug is.
- `scenarios/morning_after.py` builds, in a new folder, the state on the morning after a night run that cannot be repeated (the sales system has moved on; nothing was logged); with `--record`, last night's run is recorded with Ormaos.

**Written only for the demo.** It must not resemble any other bug collection.

## The demo page: `docs/`

A static page, no build step, that shows without installing anything:
- the problem in two sentences;
- the agent investigating without Ormaos, and with Ormaos (asciinema recordings, embedded with the asciinema player);
- how to try it, in three commands;
- what does not exist yet.

## Rules

- No secrets in any file. No tracking scripts, no analytics, no third-party scripts except the asciinema player from a pinned CDN version.
- Describe Ormaos only with the public sentence: "Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you." No numbers that were not measured. No future plans.
- Never `push --force`, never publish anywhere, never delete outside the repository.
- Small commits in English, imperative mood.
