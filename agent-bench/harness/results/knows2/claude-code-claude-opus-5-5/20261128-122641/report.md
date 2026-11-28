# agent-bench/harness: knows2, claude-code, claude-opus-5-5

Spec `knows2-opus`: 108 runs planned, 108 run; the first attempt of every task, arm and run, all of them. Agent claude-code 2.1.322, model claude-opus-5-5, effort default, 3 per task and arm, 900 s per run, 1 at a time. Started 2026-11-28T12:26:46, finished 2026-11-28T13:30:44.

- Expectations: `expectations/knows2-opus.md`, sha256 `e01f669f341fb739694f0568eb948ac0c6ff2e41722116e6a2dedef7c69a3e27` when the run started; it has not changed since.
- Base image `sha256:3555e687d7c233daa2a0669d2ffdf6d3479fd44b9eaf5d826fb82bd360059456`, agent image `sha256:6587f63cd673bfad2c6f51a17e2d556d45a80f713a2c6f6213edd39e82950bb3`, Python 3.14.4, Docker version 29.1.3, build 29.1.3-0ubuntu4.1.
- Hosts the proxy allowed: api.anthropic.com. Tools: Bash, Read, Grep, Glob, Edit, Write. Home folder at the start of a run: .claude/.credentials.json.
- Canary before the first run: all passed. (`canary.txt`)

## Per arm

| Arm | Runs | Mean score | 95% interval | Right | Null | Wrong | Median wall time | Median tool calls | Median tokens | Cost |
|---|---|---|---|---|---|---|---|---|---|---|
| none | 27 | 0.68 | 0.54 to 0.82 | 147 | 66 | 0 | 26 s | 4 | 45,984 | $2.59 |
| raw | 27 | 0.87 | 0.79 to 0.95 | 186 | 27 | 0 | 32 s | 5 | 65,839 | $4.20 |
| ormaos | 27 | 0.95 | 0.90 to 0.99 | 202 | 10 | 1 | 33 s | 5 | 91,495 | $4.68 |
| ormaos-values | 27 | 0.95 | 0.90 to 0.99 | 202 | 11 | 0 | 36 s | 6 | 108,912 | $5.46 |

Tokens are input, output and cache tokens added up, and the cost is in US dollars, both as the agent's command line reports them; different vendors count tokens differently. With one run per arm there is no interval.

## Per task

Mean score of the runs of each task and arm.

| Task | Questions | none | raw | ormaos | ormaos-values |
|---|---|---|---|---|---|
| web-backend | 8 | 1.00 | 1.00 | 0.96 | 1.00 |
| data-pipeline | 8 | 0.25 | 0.38 | 0.96 | 0.92 |
| notebook | 8 | 0.50 | 0.62 | 0.62 | 0.62 |
| ml-training | 8 | 1.00 | 1.00 | 1.00 | 1.00 |
| rl-env | 8 | 1.00 | 1.00 | 1.00 | 1.00 |
| ai-app | 7 | 0.29 | 0.86 | 1.00 | 1.00 |
| agent-change | 8 | 1.00 | 1.00 | 1.00 | 1.00 |
| order-sync | 8 | 0.12 | 1.00 | 1.00 | 1.00 |
| freight-quote | 8 | 1.00 | 1.00 | 1.00 | 1.00 |

## Every run

| Task | Arm | Run | Score | Wall time | Tool calls | Tokens | Cost | Ended |
|---|---|---|---|---|---|---|---|---|
| web-backend | none | 1 | 1.00 | 25 s | 4 | 45,984 | $0.08 | done |
| web-backend | raw | 1 | 1.00 | 32 s | 5 | 65,839 | $0.11 | done |
| web-backend | ormaos | 1 | 0.88 | 29 s | 4 | 71,621 | $0.15 | done |
| web-backend | ormaos-values | 1 | 1.00 | 25 s | 4 | 72,546 | $0.15 | done |
| data-pipeline | none | 1 | 0.25 | 21 s | 4 | 43,059 | $0.06 | done |
| data-pipeline | raw | 1 | 0.38 | 24 s | 4 | 49,965 | $0.09 | done |
| data-pipeline | ormaos | 1 | 0.88 | 21 s | 3 | 48,237 | $0.11 | done |
| data-pipeline | ormaos-values | 1 | 0.88 | 29 s | 5 | 82,994 | $0.14 | done |
| notebook | none | 1 | 0.50 | 23 s | 4 | 48,464 | $0.08 | done |
| notebook | raw | 1 | 0.62 | 49 s | 8 | 93,867 | $0.14 | done |
| notebook | ormaos | 1 | 0.62 | 28 s | 5 | 79,689 | $0.13 | done |
| notebook | ormaos-values | 1 | 0.62 | 38 s | 7 | 137,526 | $0.19 | done |
| ml-training | none | 1 | 1.00 | 25 s | 3 | 38,371 | $0.08 | done |
| ml-training | raw | 1 | 1.00 | 32 s | 4 | 47,125 | $0.09 | done |
| ml-training | ormaos | 1 | 1.00 | 30 s | 6 | 110,711 | $0.17 | done |
| ml-training | ormaos-values | 1 | 1.00 | 32 s | 5 | 100,420 | $0.20 | done |
| rl-env | none | 1 | 1.00 | 22 s | 4 | 44,102 | $0.07 | done |
| rl-env | raw | 1 | 1.00 | 26 s | 4 | 49,212 | $0.09 | done |
| rl-env | ormaos | 1 | 1.00 | 39 s | 7 | 118,605 | $0.17 | done |
| rl-env | ormaos-values | 1 | 1.00 | 27 s | 5 | 89,359 | $0.15 | done |
| ai-app | none | 1 | 0.29 | 16 s | 3 | 33,589 | $0.05 | done |
| ai-app | raw | 1 | 0.86 | 24 s | 4 | 49,251 | $0.09 | done |
| ai-app | ormaos | 1 | 1.00 | 24 s | 4 | 69,416 | $0.14 | done |
| ai-app | ormaos-values | 1 | 1.00 | 26 s | 5 | 87,726 | $0.15 | done |
| agent-change | none | 1 | 1.00 | 26 s | 4 | 53,851 | $0.10 | done |
| agent-change | raw | 1 | 1.00 | 32 s | 5 | 71,834 | $0.13 | done |
| agent-change | ormaos | 1 | 1.00 | 29 s | 5 | 83,694 | $0.15 | done |
| agent-change | ormaos-values | 1 | 1.00 | 38 s | 7 | 169,107 | $0.25 | done |
| order-sync | none | 1 | 0.38 | 42 s | 4 | 69,974 | $0.18 | done |
| order-sync | raw | 1 | 1.00 | 50 s | 6 | 197,324 | $0.38 | done |
| order-sync | ormaos | 1 | 1.00 | 59 s | 6 | 145,204 | $0.30 | done |
| order-sync | ormaos-values | 1 | 1.00 | 59 s | 9 | 280,923 | $0.42 | done |
| freight-quote | none | 1 | 1.00 | 41 s | 5 | 91,085 | $0.19 | done |
| freight-quote | raw | 1 | 1.00 | 79 s | 10 | 265,302 | $0.42 | done |
| freight-quote | ormaos | 1 | 1.00 | 34 s | 5 | 118,584 | $0.24 | done |
| freight-quote | ormaos-values | 1 | 1.00 | 35 s | 5 | 112,810 | $0.23 | done |
| web-backend | none | 2 | 1.00 | 23 s | 4 | 45,915 | $0.07 | done |
| web-backend | raw | 2 | 1.00 | 28 s | 4 | 55,338 | $0.11 | done |
| web-backend | ormaos | 2 | 1.00 | 24 s | 4 | 67,380 | $0.13 | done |
| web-backend | ormaos-values | 2 | 1.00 | 27 s | 4 | 72,988 | $0.15 | done |
| data-pipeline | none | 2 | 0.25 | 27 s | 5 | 60,453 | $0.08 | done |
| data-pipeline | raw | 2 | 0.38 | 32 s | 5 | 70,833 | $0.12 | done |
| data-pipeline | ormaos | 2 | 1.00 | 28 s | 4 | 63,803 | $0.12 | done |
| data-pipeline | ormaos-values | 2 | 1.00 | 20 s | 3 | 47,916 | $0.10 | done |
| notebook | none | 2 | 0.50 | 24 s | 4 | 45,984 | $0.07 | done |
| notebook | raw | 2 | 0.62 | 42 s | 6 | 93,393 | $0.16 | done |
| notebook | ormaos | 2 | 0.62 | 24 s | 4 | 63,647 | $0.11 | done |
| notebook | ormaos-values | 2 | 0.62 | 37 s | 7 | 151,601 | $0.24 | done |
| ml-training | none | 2 | 1.00 | 26 s | 4 | 44,029 | $0.07 | done |
| ml-training | raw | 2 | 1.00 | 30 s | 4 | 45,853 | $0.07 | done |
| ml-training | ormaos | 2 | 1.00 | 29 s | 5 | 95,422 | $0.17 | done |
| ml-training | ormaos-values | 2 | 1.00 | 40 s | 6 | 122,453 | $0.20 | done |
| rl-env | none | 2 | 1.00 | 24 s | 4 | 44,027 | $0.06 | done |
| rl-env | raw | 2 | 1.00 | 33 s | 6 | 71,306 | $0.09 | done |
| rl-env | ormaos | 2 | 1.00 | 40 s | 6 | 98,596 | $0.15 | done |
| rl-env | ormaos-values | 2 | 1.00 | 32 s | 6 | 101,314 | $0.15 | done |
| ai-app | none | 2 | 0.29 | 19 s | 3 | 33,702 | $0.05 | done |
| ai-app | raw | 2 | 0.86 | 24 s | 4 | 48,353 | $0.08 | done |
| ai-app | ormaos | 2 | 1.00 | 28 s | 5 | 83,523 | $0.13 | done |
| ai-app | ormaos-values | 2 | 1.00 | 36 s | 6 | 108,912 | $0.16 | done |
| agent-change | none | 2 | 1.00 | 24 s | 4 | 48,087 | $0.07 | done |
| agent-change | raw | 2 | 1.00 | 28 s | 4 | 53,203 | $0.09 | done |
| agent-change | ormaos | 2 | 1.00 | 33 s | 5 | 80,826 | $0.14 | done |
| agent-change | ormaos-values | 2 | 1.00 | 42 s | 6 | 121,009 | $0.20 | done |
| order-sync | none | 2 | 0.00 | 50 s | 5 | 90,836 | $0.19 | done |
| order-sync | raw | 2 | 1.00 | 56 s | 7 | 139,518 | $0.23 | done |
| order-sync | ormaos | 2 | 1.00 | 52 s | 7 | 151,550 | $0.29 | done |
| order-sync | ormaos-values | 2 | 1.00 | 44 s | 7 | 193,443 | $0.37 | done |
| freight-quote | none | 2 | 1.00 | 40 s | 5 | 91,469 | $0.17 | done |
| freight-quote | raw | 2 | 1.00 | 87 s | 10 | 237,559 | $0.35 | done |
| freight-quote | ormaos | 2 | 1.00 | 41 s | 5 | 117,866 | $0.24 | done |
| freight-quote | ormaos-values | 2 | 1.00 | 39 s | 6 | 133,445 | $0.21 | done |
| web-backend | none | 3 | 1.00 | 35 s | 6 | 73,477 | $0.10 | done |
| web-backend | raw | 3 | 1.00 | 44 s | 6 | 84,039 | $0.13 | done |
| web-backend | ormaos | 3 | 1.00 | 28 s | 4 | 67,267 | $0.12 | done |
| web-backend | ormaos-values | 3 | 1.00 | 28 s | 4 | 72,618 | $0.15 | done |
| data-pipeline | none | 3 | 0.25 | 26 s | 4 | 43,790 | $0.06 | done |
| data-pipeline | raw | 3 | 0.38 | 31 s | 5 | 63,107 | $0.10 | done |
| data-pipeline | ormaos | 3 | 1.00 | 27 s | 4 | 62,475 | $0.12 | done |
| data-pipeline | ormaos-values | 3 | 0.88 | 31 s | 4 | 66,545 | $0.13 | done |
| notebook | none | 3 | 0.50 | 32 s | 5 | 66,631 | $0.10 | done |
| notebook | raw | 3 | 0.62 | 44 s | 5 | 67,633 | $0.11 | done |
| notebook | ormaos | 3 | 0.62 | 36 s | 6 | 96,060 | $0.13 | done |
| notebook | ormaos-values | 3 | 0.62 | 40 s | 6 | 118,447 | $0.18 | done |
| ml-training | none | 3 | 1.00 | 27 s | 3 | 34,838 | $0.06 | done |
| ml-training | raw | 3 | 1.00 | 38 s | 5 | 62,619 | $0.09 | done |
| ml-training | ormaos | 3 | 1.00 | 41 s | 5 | 110,893 | $0.22 | done |
| ml-training | ormaos-values | 3 | 1.00 | 40 s | 5 | 94,396 | $0.18 | done |
| rl-env | none | 3 | 1.00 | 29 s | 4 | 43,995 | $0.07 | done |
| rl-env | raw | 3 | 1.00 | 28 s | 4 | 55,024 | $0.10 | done |
| rl-env | ormaos | 3 | 1.00 | 41 s | 5 | 86,568 | $0.15 | done |
| rl-env | ormaos-values | 3 | 1.00 | 36 s | 6 | 101,545 | $0.15 | done |
| ai-app | none | 3 | 0.29 | 20 s | 3 | 33,651 | $0.05 | done |
| ai-app | raw | 3 | 0.86 | 31 s | 4 | 54,766 | $0.10 | done |
| ai-app | ormaos | 3 | 1.00 | 39 s | 5 | 91,495 | $0.16 | done |
| ai-app | ormaos-values | 3 | 1.00 | 33 s | 5 | 88,109 | $0.14 | done |
| agent-change | none | 3 | 1.00 | 27 s | 4 | 48,023 | $0.07 | done |
| agent-change | raw | 3 | 1.00 | 34 s | 4 | 56,680 | $0.11 | done |
| agent-change | ormaos | 3 | 1.00 | 34 s | 5 | 97,469 | $0.18 | done |
| agent-change | ormaos-values | 3 | 1.00 | 51 s | 7 | 176,090 | $0.27 | done |
| order-sync | none | 3 | 0.00 | 44 s | 5 | 87,868 | $0.17 | done |
| order-sync | raw | 3 | 1.00 | 65 s | 6 | 159,131 | $0.34 | done |
| order-sync | ormaos | 3 | 1.00 | 69 s | 8 | 203,745 | $0.32 | done |
| order-sync | ormaos-values | 3 | 1.00 | 72 s | 10 | 284,276 | $0.37 | done |
| freight-quote | none | 3 | 1.00 | 45 s | 5 | 91,771 | $0.18 | done |
| freight-quote | raw | 3 | 1.00 | 72 s | 9 | 189,490 | $0.28 | done |
| freight-quote | ormaos | 3 | 1.00 | 42 s | 5 | 116,054 | $0.25 | done |
| freight-quote | ormaos-values | 3 | 1.00 | 38 s | 6 | 150,968 | $0.25 | done |

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
