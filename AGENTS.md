# AGENTS.md — ormaos-examples

## What this repository is

Example programs for Ormaos, and the hackathon demo page (in `docs/`, published at ormaos.com/demo with Cloudflare Pages). Public, Apache 2.0. Ormaos itself lives in the sibling repository `ormaos-python`; install it with `pip install -e ../ormaos-python`.

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

## The second demo app: `freight-quote/`

A scheduled Python job that quotes the freight of tomorrow's shipments.

- **Input:** a dispatch list (CSV) and a carrier's rate API: a fake local HTTP API (standard library `http.server`, started by the script), whose state is one JSON file.
- **Output:** one quote per shipment in a local SQLite database; each run replaces them.
- **The bug, on purpose:** when the carrier refuses a call (429: the account's calls for the day are used up), a `try/except Exception: log.warning(...)` prices the shipment from the contract rate card, `ratecard.csv`, which is older and lower than the carrier's tariff. The job prints "quotes finished: OK" and exits 0, and those quotes are too low.
- Standard library only, five modules (`job`, `shipments`, `carrier`, `ratecard`, `quotes`), with a README that describes it as a normal job and a `reset.sh`.
- Other code paths that also change a price and are correct: the volume weight, the half-kilo rounding, the express factor, the minimum charge. Nothing in `freight-quote/` says where the bug is.
- `scenarios/two_nights.py` builds, in a new folder, the morning after a good night and a bad night; with `--record`, both runs are recorded with Ormaos (`r1`, `r2`), for `ormaos diff`.

## One program per kind of developer: `use-cases/`

Seven small programs: `web-backend` (FastAPI, SQLite), `data-pipeline` (pandas), `notebook` (Jupyter, nbclient), `ml-training` (PyTorch on CPU), `rl-env`, `ai-app` (a local stand-in for a model API) and `agent-change` (a repository and a change an agent made).

- Each is a normal program with a README that presents it as one, the standard library plus only the library its kind needs, runnable from a copy of its folder.
- Each has one execution in which something happened that its output does not say. `scenario.py` records it with Ormaos; `questions.json` has 5 to 8 factual questions about what happened, and `demo.txt` one `ormaos` command with its output.
- The answer of every question is computed by an independent oracle in `scenario.py` (a second execution under `sys.settrace`, counters), never by reading the recording. `scenario.py <folder> --check` compares with the committed answers; CI runs it.
- The questions ask what happened, not whether it should have: Ormaos shows, the reader decides.

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

## Done means documented

- A change is done only when every document it affects is updated in the same push: this repository's `README.md` and `AGENTS.md`, and the pages of https://docs.ormaos.com that describe it.
- The docs live in `ormaos/docs` (`content/`). For a change here, the docs need `sources.json` bumped to the new commit and `python3 scripts/generate.py` run, then `python3 scripts/generate.py --check`.
- When the doc to update is in another repository than the one being changed, the report of the session says which page needs which change.
