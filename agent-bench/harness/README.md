# agent-bench/harness

A controlled place where any coding agent command line runs the same benchmark tasks under the same conditions: the same container, the same network, the same task text, the same tools, the same grading, the same record of the run, and the same rules about what counts.

Today there is one adapter, for Claude Code, and one benchmark, [`../knows2`](../knows2). Adapters for other command lines are added as one file and one container layer each; nothing else changes.

```bash
(cd ../knows2 && python3 build.py)             # the folders and the oracle's answers, on the day of the run
python3 harness.py run specs/smoke.toml        # canary, every run of the spec, report
python3 harness.py check                       # every results folder still fits its run; writes nothing
python3 -m unittest discover -s tests          # the tests of every rule below
```

Needs Linux, Python 3.11 or newer, podman or docker (whichever is installed; only docker was tried), what `knows2` needs to build, and the agent's command line logged in on this machine.

## What is the same for every agent

**1. The environment.** One base image ([`image/Containerfile`](image/Containerfile)): Ubuntu pinned by digest, its Python (the one the tasks are built with; the runner refuses another), uv pinned by digest, curl and git. An agent adds one layer that holds only its command line, at a pinned version (`adapters/<agent>.Containerfile`). The task folder is mounted at `/srv/<task>`, as in `knows2`. Every line of `results.jsonl` has the ids of both images; `run.json` has their layers.

**2. The network.** The containers of a batch are on a network without a route out. The only other thing on it is a proxy the harness runs ([`core/proxy.py`](core/proxy.py)): it answers `CONNECT host:443` for the hosts the adapter lists, word for word, and refuses everything else. No wildcards: an adapter with one does not load. Before every batch a canary runs in the agent's image, on that network, with the environment and the home folder of a run ([`image/canary.sh`](image/canary.sh)): `https://github.com` and `https://raw.githubusercontent.com` must fail, through the proxy and without it; the model's host must answer through the proxy; then the agent itself must answer one sentence with the tools of its adapter and nothing else connected. If one line does not say PASS, no run starts. The canary's output is kept in `canary.txt`, and what the proxy refused during the batch in `proxy.jsonl`.

**3. The request.** One task text per benchmark and arm, with no vendor's name in it: for `knows2`, the texts of its own runner, unchanged. The text is the whole request. The runner refuses a task folder that holds `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` or any other agent configuration (the list is `AGENT_FILES` and `AGENT_FOLDERS` in [`core/runner.py`](core/runner.py)), at any depth.

**4. The tools.** A shell, and reading, searching and editing files. No MCP server, no plugin, no web search or fetch tool, no memory. What the command line says it started with is compared with the adapter's list in the canary and again in every run. Every run gets a new home folder that holds the agent's credential file, read-only, and nothing else; it is deleted after the run. **The agent can read its own credential there.** For Claude Code the copy holds the access token only: not the refresh token, and not the tokens of other services that the file on this machine also holds. If an agent prints the credential, the runner removes it from the streams and the work folder and says so in the result.

The copy cannot be renewed inside a run, so the runner reads when it expires before every run. A run does not start with a credential that expires within 20 minutes: the batch stops before it, the runs under way end, and the runs that have not started stay "not started" (not failures, not dropped). The runner prints how to renew the credential on this machine (for Claude Code, `claude -p ok`) and the command that continues the batch, `python3 harness.py run <spec> --continue <results folder>`. Continuing checks that it is the same batch (spec, expectations, adapter, images, task folders, oracle), runs the canary again, and starts only the runs that never started.

**5. The grading.** Outside the container, after it has ended, by the benchmark's own oracle and rules. The grader is a separate process ([`core/grading.py`](core/grading.py)) that gets a copy of the work folder in a place whose name says nothing, the task, and the oracle's answers. It is not told the agent, the model or where the results go.

**6. The record.** An adapter turns what its command line prints into one schema of events ([`EVENTS.md`](EVENTS.md)): assistant text, tool call, tool result, final, and usage (input, output and cache tokens, the cost if the command line reports one, the wall time on the runner's clock). The numbers of a result come from the events, and the report checks that they still agree. What the command line printed is kept in `streams/` for people; reports and pages do not read it.

**7. The rules.** A run is described by a spec ([`specs/`](specs)): benchmark, tasks, arms, agent, model, effort, n, time limit. The runner refuses to start unless `expectations/<spec name>.md` exists: what is expected of the run, written before it. Its sha256 goes into `run.json`, and the report and `harness.py check` fail for a results folder whose expectations file has changed since. The first attempt of every task, arm and run counts. Nothing is run again: a batch that stopped is continued with the runs that never started, and a run that started is never started again. A run that ended with an error or ran out of time counts with what it left; in a finished batch, a planned run without a result fails the report.

`python3 harness.py check` fails for a results folder that no longer fits its run (expectations changed, a result dropped or doubled, events that do not fit, a `report.md` that is not what the files say). The build of the benchmark pages ([`site/benchmarks/build.py`](../../site/benchmarks/build.py)) runs the same check on every committed results folder, and CI runs both.

## The results

`results/<benchmark>/<agent>-<model>/<time>/` has what a results folder of `knows2` has (`build.json`, `oracle/`, `results.jsonl`, `report.md`, `streams/`, `work/`) and:

- `events/`: the event stream of every run;
- `run.json`: the spec, the sha256 of the expectations, the images, the agent's hosts, tools and home folder, the canary, the plan, and every time the batch stopped and was continued;
- `canary.txt`, `expectations.md` (a copy, as it was), `proxy.jsonl`.

Results folders are committed whole, the way `knows2` commits its own: the streams, the events, the answers and the work folder each agent left, with the `.ormaos/` recording an Ormaos arm read (the repository's `.gitignore` leaves `.ormaos/` out everywhere else; [`.gitignore`](.gitignore) here takes it back in). Left out of a work folder:

- `.venv/`: inside the container it is the `ormaos` command line, mounted read-only from `knows2/.build/`; in the copy it is an empty folder. `build.json` names the Ormaos commit it was built from.
- `result.json`, the trace of the `raw` arm: the same file in every run of the arm, taken out after grading, as `knows2` does. `build.json` has its size.
- `.ormaos/.gitignore`: `ormaos run` writes it so that recordings stay on the machine; it is taken out after grading, or git would leave the recording out.
- `.git/`, the history an `agent-change` folder comes with: git takes a folder that holds its own `.git` for a link to another repository and leaves its files out, so they are committed without it, as `knows2` commits them.
- Folders whose name starts with `_` under `results/`: scratch.

A spec with `test = true` is a test of the harness: its results folder gets `TEST.md`, its report says so, and the benchmark pages do not show it. `results/knows2/claude-code-claude-opus-5-5/20261127-192608` is one (the smoke test).

`results/knows2/claude-code-claude-opus-5-5/20261128-122641` is the first full run (spec [`knows2-opus`](specs/knows2-opus.toml), expectations [`knows2-opus.md`](expectations/knows2-opus.md)): 108 of 108 runs, Claude Code 2.1.322 with `claude-opus-5-5`, 2026-11-28. Mean score, with its 95% interval: none 0.68 (0.54 to 0.82), raw 0.87 (0.79 to 0.95), ormaos 0.95 (0.90 to 0.99), ormaos-values 0.95 (0.90 to 0.99); right, null and wrong answers: none 147, 66, 0; raw 186, 27, 0; ormaos 202, 10, 1; ormaos-values 202, 11, 0. The proxy refused only the canary's three requests. Its [`report.md`](results/knows2/claude-code-claude-opus-5-5/20261128-122641/report.md) has every run.

The benchmark pages take their headline and their charts from the most recent complete run of the harness, and show every results folder on its own, labelled with its environment and agent: a run of the harness and a run of `knows2`'s own runner are never added up. The knows2 page also has the run's expectations, verbatim, with each line checked where it is a number.

A line of `results.jsonl` has the keys of a `knows2` line, without `ran_again` and `named_outside` (they are read from Claude Code's own output there), with `cli_version` in the place of `claude`, and with `agent`, `effort`, `final`, `violations`, `exit_code`, `images` and `events`.

## Adding an adapter

Two files in [`adapters/`](adapters), and nothing else:

1. `<agent>.Containerfile`: `FROM ${BASE}` and one `RUN` that installs the command line at a pinned version, and checks what it installed.
2. `<agent>.py` with `ADAPTER`, an instance of a subclass of `Adapter` ([`adapters/__init__.py`](adapters/__init__.py)) that says:
   - `name`, `cli_version`, `build_args`;
   - `hosts`: the hosts it needs to reach the model, found by running it behind the proxy and reading `proxy.jsonl`; and `probe`, a URL on the model's host for the canary;
   - `tools`: its own name of every tool it is given, each a `shell` or a `file` tool; `efforts`; `env`;
   - `home_files`: its credential file, cut down to what a run needs; `secrets`; `credential_seconds`, read from that copy; `renew`, the command that renews it on this machine;
   - `argv`: the command line for one task text, with every other tool, MCP, memory and customization turned off;
   - `parser`: its output, line by line, into the events of `EVENTS.md`.

Then a spec with `agent = "<agent>"`, and a test file like the Claude Code parts of `tests/test_4_tools.py` and `tests/test_6_record.py`. An adapter is not finished until the canary passes and a smoke spec has run with it.

## What is not controlled yet

- **The model's own randomness.** The same request does not give the same run twice, and the command lines do not all take a seed or a temperature. Only more runs per slot answer this.
- **Tokens.** Different vendors count tokens differently, cache differently and price differently. `usage` is each vendor's own count; token numbers of two vendors are not on one scale. Wall time is the runner's clock for all.
- **What each command line adds to the request**: its system prompt, its tool descriptions, its own loop. The harness makes the task text and the tool kinds the same, not these.
- **Effort.** `effort = "default"` is each command line's own default, and the levels of two vendors are not the same thing.
- **The model's host.** Its load and its rate limits at the time of the run are not the harness's.
- **Inside the allowed host.** The proxy does not read the traffic: whatever the vendor's own API offers on that host (a tool that runs on the vendor's servers, for example) is limited only by the tools the command line is given.
- **The Ubuntu packages** of the base image are not pinned; the image id in the results says which build ran.
- **The credential** is readable by the agent, as said above.
