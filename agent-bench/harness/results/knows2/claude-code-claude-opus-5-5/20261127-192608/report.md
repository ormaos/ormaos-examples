# agent-bench/harness: knows2, claude-code, claude-opus-5-5

**A test of the harness, not a result.** Nothing may be concluded from its scores.

Spec `smoke`: 4 runs planned, 4 run; the first attempt of every task, arm and run, all of them. Agent claude-code 2.1.322, model claude-opus-5-5, effort default, 1 per task and arm, 900 s per run, 1 at a time. Started 2026-11-27T19:26:13, finished 2026-11-27T19:29:32.

- Expectations: `expectations/smoke.md`, sha256 `27ea3c80f6ecebd7d86ef8cfceb692ee9bf13242d3890a20f5ae35da05ce5e62` when the run started; it has not changed since.
- Base image `sha256:3555e687d7c233daa2a0669d2ffdf6d3479fd44b9eaf5d826fb82bd360059456`, agent image `sha256:6587f63cd673bfad2c6f51a17e2d556d45a80f713a2c6f6213edd39e82950bb3`, Python 3.14.4, Docker version 29.1.3, build 29.1.3-0ubuntu4.1.
- Hosts the proxy allowed: api.anthropic.com. Tools: Bash, Read, Grep, Glob, Edit, Write. Home folder at the start of a run: .claude/.credentials.json.
- Canary before the first run: all passed. (`canary.txt`)

## Per arm

| Arm | Runs | Mean score | 95% interval | Right | Null | Wrong | Median wall time | Median tool calls | Median tokens | Cost |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 1 | 0.12 | - | 1 | 4 | 3 | 43 s | 5 | 91,350 | $0.19 |
| raw | 1 | 1.00 | - | 8 | 0 | 0 | 58 s | 8 | 162,081 | $0.32 |
| ormaos | 1 | 1.00 | - | 8 | 0 | 0 | 44 s | 6 | 147,737 | $0.29 |
| ormaos-values | 1 | 1.00 | - | 8 | 0 | 0 | 54 s | 8 | 248,718 | $0.40 |

Tokens are input, output and cache tokens added up, and the cost is in US dollars, both as the agent's command line reports them; different vendors count tokens differently. With one run per arm there is no interval.

## Per task

Mean score of the runs of each task and arm.

| Task | Questions | none | raw | ormaos | ormaos-values |
|---|---|---|---|---|---|
| order-sync | 8 | 0.12 | 1.00 | 1.00 | 1.00 |

## Every run

| Task | Arm | Run | Score | Wall time | Tool calls | Tokens | Cost | Ended |
|---|---|---|---|---|---|---|---|---|
| order-sync | none | 1 | 0.12 | 43 s | 5 | 91,350 | $0.19 | done |
| order-sync | raw | 1 | 1.00 | 58 s | 8 | 162,081 | $0.32 | done |
| order-sync | ormaos | 1 | 1.00 | 44 s | 6 | 147,737 | $0.29 | done |
| order-sync | ormaos-values | 1 | 1.00 | 54 s | 8 | 248,718 | $0.40 | done |

## Not as planned

Nothing: every planned run has a result, with the tools and the network of the plan.

## Refused by the proxy

Every target the proxy refused during the batch, the canary's included, with how often.

- `github.com:443`: 1
- `http://example.com/`: 1
- `raw.githubusercontent.com:443`: 1

## Not controlled

- The model's own randomness: the same request does not give the same run twice.
- Tokens and cost are each vendor's own count.
- The agent can read its own credential in its home folder.
- The system prompt and the tool descriptions are each command line's own.
