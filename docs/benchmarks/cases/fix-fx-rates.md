# fx-rates, in fix

*Situation · fix*

A scheduled job. By its README, it takes over exchange rates from a feed. Source: [`agent-bench/bugs/fx-rates/task`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/bugs/fx-rates/task).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Passed the check, first attempts:

- 2026-11-26, `claude-code / claude-opus-5-5`, bubblewrap, network open: `none` 1/3, `raw` 3/3, `ormaos` 3/3 (3 runs per arm)

## What happened

That night cron ran `python3 job.py`; it printed `rates finished: OK` and exited with code 0. This morning 4 currencies still have the rate of the day before: `CAD`, `CHF`, `JPY` and `PLN`. Where it behaved otherwise than its README: a retry that makes its call once.

The items are those the scenario's own check of the data found, in [`build.json`](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/build.json).

The symptom, from `TASK.md` in the agent's folder:

```text
Last night's rates run said OK, but this morning some currencies still have the rate published the day before, though the feed has a newer one.
```

## What the agent was given

Its folder (the code, its README, `TASK.md` and the data that night left, with what the arm adds) and the task text, the same in every arm but for the arm's last sentence:

`none`:

```text
Last night's rates run said OK, but this morning some currencies still have the rate published the day before, though the feed has a newer one. The job runs from cron with `python3 job.py`. Find the cause and fix it.
```

`raw`:

```text
Last night's rates run said OK, but this morning some currencies still have the rate published the day before, though the feed has a newer one. The job runs from cron with `python3 job.py`. Find the cause and fix it. A VizTracer trace of that run is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
Last night's rates run said OK, but this morning some currencies still have the rate published the day before, though the feed has a newer one. The job runs from cron with `python3 job.py`. Find the cause and fix it. That run was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the first 15 lines of its output, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-none-1.jsonl)
- Passed the check
- 5 tool calls, 74,050 tokens, 43 s

Commands, in order (5):

1. ```text
   ls -la && cat job.py
   ```
2. ```text
   cat README.md TASK.md currencies.txt feed.py rates.py retry.py; ls -la data; cat data/feed.json | head -50
   ```
3. ```text
   cat data/cron.log; echo ---; python3 rates.py; python3 -c "import retry; print(retry.RETRY_STATUSES, 503 in retry.RETRY_STATUSES)"
   ```
4. ```text
   Edit retry.py
   ```
5. ```text
   T=$(mktemp -d) && cp data/rates.db $T/ && python3 - "$T" <<'EOF'
   import json,sys
   s=json.load(open("data/feed.json")); s["busy"]={"CAD":1,"CHF":2,"JPY":3}
   json.dump(s,open(sys.argv[1]+"/feed.json","w"))
   EOF
   FX_RATES_LOG_LEVEL=INFO python3 job.py --db $T/rates.db --feed $T/feed.json; echo exit=$?; python3 rates.py --db $T/rates.db
   ```

Its change, against `task/`

```text
--- task/retry.py
+++ retry.py
@@ -9,7 +9,12 @@
 ATTEMPTS = int(os.environ.get("FX_RATES_ATTEMPTS", "3"))
 WAIT_SECONDS = float(os.environ.get("FX_RATES_WAIT_SECONDS", "0.2"))
 # The answers that mean "busy, ask again": bad gateway, unavailable, timeout.
-RETRY_STATUSES = os.environ.get("FX_RATES_RETRY_STATUSES", "502,503,504").split(",")
+# Parsed to ints: FeedError.status is the HTTP code as an int.
+RETRY_STATUSES = frozenset(
+    int(status)
+    for status in os.environ.get("FX_RATES_RETRY_STATUSES", "502,503,504").split(",")
+    if status.strip()
+)
 
 log = logging.getLogger("fx_rates.retry")
 
```

What the check said

```text
pass  the feed is busy once for four currencies: exit 0, not as expected: none
pass  the feed is never busy: exit 0, not as expected: none
pass  a currency stays busy and another is not carried: exit 0, not as expected: none, 3 attempts
fixed
```

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-raw-1.jsonl)
- Passed the check
- 5 tool calls, 63,883 tokens, 38 s

Commands, in order (5):

1. ```text
   ls -la && cat job.py && ls -R | head -50
   ```
2. ```text
   cat README.md TASK.md currencies.txt feed.py rates.py retry.py data/cron.log; head -c 1500 data/feed.json
   ```
3. ```text
   python3 -I - <<'EOF'
   import json, collections
   ev = json.load(open("result.json"))["traceEvents"]
   c = collections.Counter(e.get("name") for e in ev)
   for n,k in c.items():
       if any(s in n for s in ("latest","worth_retrying","store","update","sleep","call (","FeedError","send_error")): print(k, n)
   for e in ev:
       n=e.get("name","")
       if n.startswith(("latest","worth_retrying","update")) or "time.sleep" in n or n.startswith("store"):
           print(e["ts"], e.get("dur"), n, e.get("args",""))
   EOF
   python3 rates.py
   ```
4. ```text
   Edit retry.py
   ```
5. ```text
   T=$(mktemp -d) && cp data/rates.db $T/ && python3 - "$T" <<'EOF'
   import json,sys
   s=json.load(open("data/feed.json")); s["busy"]={"CHF":1,"JPY":2,"PLN":1,"CAD":1,"USD":5}
   json.dump(s,open(sys.argv[1]+"/feed.json","w"))
   EOF
   FX_RATES_LOG_LEVEL=INFO python3 job.py --db $T/rates.db --feed $T/feed.json; echo exit=$?; python3 rates.py --db $T/rates.db
   ```

Its change, against `task/`

```text
--- task/retry.py
+++ retry.py
@@ -9,7 +9,12 @@
 ATTEMPTS = int(os.environ.get("FX_RATES_ATTEMPTS", "3"))
 WAIT_SECONDS = float(os.environ.get("FX_RATES_WAIT_SECONDS", "0.2"))
 # The answers that mean "busy, ask again": bad gateway, unavailable, timeout.
-RETRY_STATUSES = os.environ.get("FX_RATES_RETRY_STATUSES", "502,503,504").split(",")
+# HTTP status codes are ints (FeedError.status), so parse the list into ints.
+RETRY_STATUSES = frozenset(
+    int(status)
+    for status in os.environ.get("FX_RATES_RETRY_STATUSES", "502,503,504").split(",")
+    if status.strip()
+)
 
 log = logging.getLogger("fx_rates.retry")
 
```

What the check said

```text
pass  the feed is busy once for four currencies: exit 0, not as expected: none
pass  the feed is never busy: exit 0, not as expected: none
pass  a currency stays busy and another is not carried: exit 0, not as expected: none, 3 attempts
fixed
```

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-ormaos-1.jsonl)
- Passed the check
- 6 tool calls, 96,890 tokens, 40 s

Commands, in order (6):

1. ```text
   .venv/bin/ormaos guide; ls -la; ls -la .ormaos
   ```

   Output, the first 15 of 68 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-ormaos-1.jsonl?plain=1#L5)):

   ```text
   ormaos: what happened inside a Python run, to read instead of guessing.
   
   WHEN TO USE IT
   - A Python program runs, and its output does not explain what it did: a job
     that prints OK, an error that never shows, a result you cannot trace.
   - You want to see what ran: the project's calls with the shape of their
     arguments, every exception (also the caught ones), the SQL statements,
     files, subprocesses and HTTP requests.
   
   WHERE TO START
   1. Record:  ormaos run -- <command>
      The command runs unchanged (same output, same exit code); its Python must
      have ormaos installed. In a script or notebook: `with ormaos.record():`.
   2. Read the summary printed on stderr: at most 5 lines, each starting with
      "ormaos:". To see it again, with more: ormaos show
   ```
2. ```text
   .venv/bin/ormaos show; .venv/bin/ormaos exceptions last; cat TASK.md README.md currencies.txt; ls -la data
   ```

   Output, the first 15 of 91 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-ormaos-1.jsonl?plain=1#L8)):

   ```text
   r1 exit 0 in 0.62s: 1 Python process, 100 calls, 9 exceptions (4 swallowed, 0 uncaught)
   command: .venv/bin/python job.py
   swallowed 4x feed.FeedError at job.py:48 in update, raised at feed.py:41  [r1:e2]
   io: 69 events (file 22, sqlite 35, http 12)
   not collected: io: reads of the 1 file opened at job.py:39: opened for reading, and no `read` call by Python code was seen on a file of that name: if it was read, that was inside C code (a file that is iterated, `for line in f`, `csv.reader`)
   not collected: io: sockets, at feed.py:86 (once): a socket was connected or bound there; sockets are not recorded, only HTTP made through http.client or httpx is
   never recorded: values, and 13 more kinds of things (`ormaos show --json` lists them with the reason)
   next: ormaos exceptions r1:e2 | ormaos tree r1:c1 | ormaos io r1
   r1: 9 exceptions (4 swallowed, 0 uncaught)
   r1:e2 swallowed feed.FeedError  raised at feed.py:41  handled at job.py:48 in update
   r1:e4 swallowed feed.FeedError  raised at feed.py:41  handled at job.py:48 in update
   r1:e6 swallowed feed.FeedError  raised at feed.py:41  handled at job.py:48 in update
   r1:e8 swallowed feed.FeedError  raised at feed.py:41  handled at job.py:48 in update
   r1:e1 replaced urllib.error.HTTPError  raised at /usr/lib/python3.14/urllib/request.py:611  handled at feed.py:40 in latest
   r1:e3 replaced urllib.error.HTTPError  raised at /usr/lib/python3.14/urllib/request.py:611  handled at feed.py:40 in latest
   ```
3. ```text
   cat job.py feed.py retry.py rates.py data/cron.log data/feed.json; .venv/bin/ormaos exceptions r1:e1; .venv/bin/ormaos io r1 --kind http
   ```

   Output, the first 15 of 336 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-ormaos-1.jsonl?plain=1#L10)):

   ```text
   """fx-rates: take over today's exchange rates from the feed.
   
   Meant to run on a schedule (see README.md)::
   
       python job.py
   
   For every currency in currencies.txt it asks the feed for the latest rate
   and stores it. Exit code 0 means the run is done; anything else means the
   job could not run.
   """
   
   import argparse
   import logging
   import os
   import sys
   ```
4. ```text
   .venv/bin/python rates.py
   ```
5. ```text
   Edit retry.py
   ```
6. ```text
   T=$(mktemp -d) && cp data/rates.db $T/ && python3 -c "
   import json,sys;s=json.load(open('data/feed.json'));s['busy']={'CHF':1,'JPY':2,'PLN':1,'CAD':5};json.dump(s,open(sys.argv[1],'w'))" $T/feed.json && FX_RATES_LOG_LEVEL=INFO .venv/bin/python job.py --db $T/rates.db --feed $T/feed.json; echo exit=$?; .venv/bin/python rates.py --db $T/rates.db
   ```

Its change, against `task/`

```text
--- task/retry.py
+++ retry.py
@@ -9,7 +9,12 @@
 ATTEMPTS = int(os.environ.get("FX_RATES_ATTEMPTS", "3"))
 WAIT_SECONDS = float(os.environ.get("FX_RATES_WAIT_SECONDS", "0.2"))
 # The answers that mean "busy, ask again": bad gateway, unavailable, timeout.
-RETRY_STATUSES = os.environ.get("FX_RATES_RETRY_STATUSES", "502,503,504").split(",")
+# As ints: FeedError.status is the int HTTP code, so strings would never match.
+RETRY_STATUSES = {
+    int(code)
+    for code in os.environ.get("FX_RATES_RETRY_STATUSES", "502,503,504").split(",")
+    if code.strip()
+}
 
 log = logging.getLogger("fx_rates.retry")
 
```

What the check said

```text
pass  the feed is busy once for four currencies: exit 0, not as expected: none
pass  the feed is never busy: exit 0, not as expected: none
pass  a currency stays busy and another is not carried: exit 0, not as expected: none, 3 attempts
fixed
```

## Every run

The first attempt of every run of every arm.

| Arm | Run | Check | Last line | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|
| `none` | 1 | passed | `fixed` | 5 | 74,050 | 43 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-none-1.jsonl) |
| `none` | 2 | did not pass | `rates finished: WARNING held for review: HUF` | 7 | 91,607 | 50 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-none-2.jsonl) |
| `none` | 3 | did not pass | `rates finished: INCOMPLETE (held for review: HUF)` | 8 | 109,670 | 54 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-none-3.jsonl) |
| `raw` | 1 | passed | `fixed` | 5 | 63,883 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-raw-1.jsonl) |
| `raw` | 2 | passed | `fixed` | 7 | 112,326 | 48 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-raw-2.jsonl) |
| `raw` | 3 | passed | `fixed` | 5 | 74,942 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-raw-3.jsonl) |
| `ormaos` | 1 | passed | `fixed` | 6 | 96,890 | 40 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-ormaos-1.jsonl) |
| `ormaos` | 2 | passed | `fixed` | 6 | 93,700 | 36 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-ormaos-2.jsonl) |
| `ormaos` | 3 | passed | `fixed` | 6 | 94,887 | 36 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/fx-rates-ormaos-3.jsonl) |

## The results files

- The benchmark: [fix](https://ormaos.com/benchmarks/fix/)
- Results folder: [`agent-bench/results/20261126-220703`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703): 2026-11-26, `claude-code / claude-opus-5-5`, bubblewrap, network open
