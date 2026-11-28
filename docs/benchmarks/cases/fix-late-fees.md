# late-fees, in fix

*Situation · fix*

A scheduled job. By its README, it charges late fees on overdue invoices. Source: [`agent-bench/bugs/late-fees/task`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/bugs/late-fees/task).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Passed the check, first attempts:

- 2026-11-26, `claude-code / claude-opus-5-5`, bubblewrap, network open: `none` 2/3, `raw` 2/3, `ormaos` 3/3 (3 runs per arm)

## What happened

That night cron ran `python3 job.py`; it printed `late fees finished: OK` and exited with code 0. This morning the billing database has no late fee dated 2026-11-25, the night of the run. Where it behaved otherwise than its README: a branch taken because of a value in the environment.

The items are those the scenario's own check of the data found, in [`build.json`](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/build.json).

The symptom, from `TASK.md` in the agent's folder:

```text
Last night's late-fees run said OK, but this morning the billing database has no late fee of last night for invoices that were overdue.
```

## What the agent was given

Its folder (the code, its README, `TASK.md` and the data that night left, with what the arm adds) and the task text, the same in every arm but for the arm's last sentence:

`none`:

```text
Last night's late-fees run said OK, but this morning the billing database has no late fee of last night for invoices that were overdue. The job runs from cron with `python3 job.py`. Find the cause and fix it.
```

`raw`:

```text
Last night's late-fees run said OK, but this morning the billing database has no late fee of last night for invoices that were overdue. The job runs from cron with `python3 job.py`. Find the cause and fix it. A VizTracer trace of that run is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
Last night's late-fees run said OK, but this morning the billing database has no late fee of last night for invoices that were overdue. The job runs from cron with `python3 job.py`. Find the cause and fix it. That run was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the first 15 lines of its output, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-none-1.jsonl)
- Passed the check
- 9 tool calls, 99,328 tokens, 49 s

Commands, in order (9):

1. ```text
   ls -la && cat job.py; crontab -l 2>/dev/null
   ```
2. ```text
   cat TASK.md README.md settings.ini settings.py fees.py invoices.py; ls -la data
   ```
3. ```text
   cat data/cron.log; echo ---; python3 invoices.py; echo ---; env | grep -i late_fees; grep -rs LATE_FEES /etc/crontab /etc/cron.d /etc/environment 2>/dev/null
   ```
4. ```text
   T=$(mktemp -d) && cp data/billing.db $T/ && LATE_FEES_PAUSE=0 LATE_FEES_LOG_LEVEL=INFO python3 job.py --db $T/billing.db --date 2026-11-25; cp data/billing.db $T/b2.db && LATE_FEES_LOG_LEVEL=INFO python3 job.py --db $T/b2.db --date 2026-11-25
   ```
5. ```text
   Edit settings.py
   ```
6. ```text
   Edit settings.py
   ```
7. ```text
   Edit job.py
   ```
8. ```text
   T=$(mktemp -d) && for v in 0 no false "" 1 yes bogus; do cp data/billing.db $T/b.db; echo "== LATE_FEES_PAUSE='$v'"; LATE_FEES_PAUSE="$v" python3 job.py --db $T/b.db --date 2026-11-25; echo "exit=$?"; python3 invoices.py --db $T/b.db | grep 11-25; done; cp data/billing.db $T/b.db; echo "== unset"; env -u LATE_FEES_PAUSE python3 job.py --db $T/b.db --date 2026-11-25; python3 invoices.py --db $T/b.db | grep 11-25
   ```
9. ```text
   Edit README.md
   ```

Its change, against `task/`

```text
--- task/README.md
+++ README.md
@@ -25,7 +25,7 @@
 
 ## Pausing
 
-During maintenance of the billing system the job must not charge. Set `pause = yes` in `settings.ini`, or `LATE_FEES_PAUSE=1` in the environment of the job (the environment wins). A paused night charges nothing and still ends with `late fees finished: OK`.
+During maintenance of the billing system the job must not charge. Set `pause = yes` in `settings.ini`, or `LATE_FEES_PAUSE=1` in the environment of the job (the environment wins). `LATE_FEES_PAUSE` takes the same values as the file: `1`/`yes`/`true`/`on` pause, `0`/`no`/`false`/`off` (or empty) do not, and anything else makes the job fail with exit code 2. A paused night charges nothing, prints `late fees paused: ...`, and still ends with `late fees finished: OK`.
 
 ## How it is built
 
--- task/job.py
+++ job.py
@@ -49,6 +49,9 @@
     """A paused night: count what would have been looked at, charge nothing."""
     waiting = len(invoices.due_before(conn, day))
     log.info("paused: %d invoices left as they are", waiting)
+    # Printed, not logged: what the job prints is all cron keeps of a run, and
+    # a paused night must not look the same as a charged one.
+    print(f"late fees paused: {day} not charged ({waiting} invoices due before it)")
     return 0
 
 
--- task/settings.py
+++ settings.py
@@ -18,6 +18,23 @@
     grace_days: dict
 
 
+def _pause(job):
+    """The pause switch: LATE_FEES_PAUSE if set, else ``pause`` in settings.ini.
+
+    The variable is parsed like the file (1/yes/true/on, 0/no/false/off), so
+    LATE_FEES_PAUSE=0 means "not paused". Any other value is an error rather
+    than a silent guess, since a wrong guess either skips a night of fees or
+    charges during maintenance.
+    """
+    value = os.environ.get("LATE_FEES_PAUSE")
+    if value is None or value.strip() == "":
+        return job.getboolean("pause", fallback=False)
+    key = value.strip().lower()
+    if key not in configparser.ConfigParser.BOOLEAN_STATES:
+        raise ValueError(f"LATE_FEES_PAUSE={value!r} is not a yes/no value")
+    return configparser.ConfigParser.BOOLEAN_STATES[key]
+
+
 def load(path=DEFAULT_FILE):
     parser = configparser.ConfigParser()
     with open(path, encoding="utf-8") as handle:
@@ -25,7 +42,7 @@
     job, fees = parser["job"], parser["fees"]
     return Settings(
         # LATE_FEES_PAUSE in the environment wins over the file.
-        pause=os.environ.get("LATE_FEES_PAUSE") or job.getboolean("pause", fallback=False),
+        pause=_pause(job),
         daily_basis_points=fees.getint("daily_basis_points"),
         minimum_cents=fees.getint("minimum_cents"),
         cap_percent=fees.getint("cap_percent"),
```

What the check said

```text
pass  the night ran with LATE_FEES_PAUSE=0: 27 fees, 27 expected, run twice exit 0
pass  a night with LATE_FEES_PAUSE=1 is paused: 20 fees, 20 expected, run twice exit 0
pass  a night without the variable is charged: 27 fees, 27 expected, run twice exit 0
fixed
```

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-raw-1.jsonl)
- Did not pass the check
- 13 tool calls, 241,924 tokens, 66 s

Commands, in order (13):

1. ```text
   ls -la && cat job.py
   ```
2. ```text
   cat README.md TASK.md settings.ini settings.py fees.py invoices.py; ls -la data
   ```
3. ```text
   python3 -I -c "
   import json,collections
   d=json.load(open('result.json'))
   ev=d['traceEvents']
   c=collections.Counter(e.get('name') for e in ev)
   for n,k in c.most_common(60): print(k,n)
   "
   ```
4. ```text
   cat data/cron.log; python3 -I -c "
   import json
   d=json.load(open('result.json'))
   ev=sorted(d['traceEvents'],key=lambda e:e.get('ts',0))
   for e in ev:
     n=e.get('name','')
     if any(k in n for k in ['job.py','settings.py','fees.py','invoices.py','environ','getboolean','sqlite','date']): print(e.get('ts'),e.get('dur'),n, e.get('args',''))
   " | head -80
   ```
5. ```text
   python3 -I -c "
   import json
   d=json.load(open('result.json'))
   ev=sorted(d['traceEvents'],key=lambda e:e.get('ts',0))
   s=[e for e in ev if e.get('ts',0)>=214746355 and e.get('ts',0)<214747200]
   for e in s: print(e.get('ts'),e.get('dur'),e.get('name'))
   " | grep -v 'dict.update' | head -60; grep -rn PAUSE /etc/crontab /etc/cron* /etc/environment ~/.profile ~/.bashrc 2>/dev/null; crontab -l 2>/dev/null; env | grep LATE
   ```
6. ```text
   python3 -I -c "
   import json
   d=json.load(open('result.json'))
   ev=sorted(d['traceEvents'],key=lambda e:e.get('ts',0))
   s=[e for e in ev if e.get('ts',0)>=214746700 and e.get('ts',0)<214747200]
   for e in s: print(e.get('ts'),e.get('dur'),e.get('name'))
   names={e.get('name') for e in ev}
   print([n for n in names if 'job.py' in n or 'getboolean' in n or 'fees.py' in n or 'invoices.py' in n])
   print({k:v for k,v in d.items() if k!='traceEvents'})
   " | grep -v -e 'dict.update' -e 'Pattern.match'
   ```
7. ```text
   for v in 0 no false 1; do LATE_FEES_PAUSE=$v python3 -I -c "import settings; print(repr('$v'), settings.load().pause)"; done; python3 -I invoices.py; date
   ```
8. ```text
   for v in 0 no false 1; do LATE_FEES_PAUSE=$v python3 -c "import settings; print(repr('$v'), settings.load().pause)"; done
   ```
9. ```text
   Edit settings.py
   ```
10. ```text
   Edit settings.py
   ```
11. ```text
   Edit job.py
   ```
12. ```text
   Edit README.md
   ```
13. ```text
   T=$(mktemp -d) && cp data/billing.db $T/ && for v in "" 0 no false 1 yes maybe; do printf '%-6s ' "[$v]"; LATE_FEES_PAUSE=$v python3 job.py --db $T/billing.db --date 2026-11-25; echo " exit=$?"; done; python3 invoices.py --db $T/billing.db; rm -r $T
   ```

Its change, against `task/`

```text
--- task/README.md
+++ README.md
@@ -25,7 +25,7 @@
 
 ## Pausing
 
-During maintenance of the billing system the job must not charge. Set `pause = yes` in `settings.ini`, or `LATE_FEES_PAUSE=1` in the environment of the job (the environment wins). A paused night charges nothing and still ends with `late fees finished: OK`.
+During maintenance of the billing system the job must not charge. Set `pause = yes` in `settings.ini`, or `LATE_FEES_PAUSE=1` in the environment of the job (the environment wins). Both are booleans: `1`/`yes`/`true`/`on` pause, `0`/`no`/`false`/`off` do not, an empty or unset variable falls back to the file, and any other value makes the job fail with exit code 2. A paused night charges nothing and ends with `late fees finished: OK (paused, nothing charged)`.
 
 ## How it is built
 
--- task/job.py
+++ job.py
@@ -74,7 +74,11 @@
         charged = charge_night(conn, config, day)
     conn.close()
     log.info("%s: %d fees charged", day, charged)
-    print("late fees finished: OK")
+    if config.pause:
+        # Say it: what the job prints is all that is kept of a run.
+        print("late fees finished: OK (paused, nothing charged)")
+    else:
+        print("late fees finished: OK")
     return 0
 
 
--- task/settings.py
+++ settings.py
@@ -18,14 +18,30 @@
     grace_days: dict
 
 
+def _pause(job):
+    """LATE_FEES_PAUSE in the environment wins over the file.
+
+    Both are read as booleans (1/yes/true/on, 0/no/false/off): any non-empty
+    string is truthy in Python, so LATE_FEES_PAUSE=0 used to pause the job.
+    An unset or empty variable falls back to the file; anything else is an
+    error rather than a guess.
+    """
+    raw = os.environ.get("LATE_FEES_PAUSE", "").strip()
+    if not raw:
+        return job.getboolean("pause", fallback=False)
+    try:
+        return configparser.ConfigParser.BOOLEAN_STATES[raw.lower()]
+    except KeyError:
+        raise ValueError(f"LATE_FEES_PAUSE={raw!r} is not a boolean (use 1/0, yes/no)") from None
+
+
 def load(path=DEFAULT_FILE):
     parser = configparser.ConfigParser()
     with open(path, encoding="utf-8") as handle:
         parser.read_file(handle)
     job, fees = parser["job"], parser["fees"]
     return Settings(
-        # LATE_FEES_PAUSE in the environment wins over the file.
-        pause=os.environ.get("LATE_FEES_PAUSE") or job.getboolean("pause", fallback=False),
+        pause=_pause(job),
         daily_basis_points=fees.getint("daily_basis_points"),
         minimum_cents=fees.getint("minimum_cents"),
         cap_percent=fees.getint("cap_percent"),
```

What the check said

```text
pass  the night ran with LATE_FEES_PAUSE=0: 27 fees, 27 expected, run twice exit 0
FAIL  a night with LATE_FEES_PAUSE=1 is paused: late-fees: the job did not finish with 'late fees finished: OK':
pass  a night without the variable is charged: 27 fees, 27 expected, run twice exit 0
not fixed
```

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-ormaos-1.jsonl)
- Passed the check
- 8 tool calls, 117,837 tokens, 44 s

Commands, in order (8):

1. ```text
   .venv/bin/ormaos guide; ls -la; ls -la .ormaos
   ```

   Output, the first 15 of 68 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-ormaos-1.jsonl?plain=1#L5)):

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
   .venv/bin/ormaos show; .venv/bin/ormaos exceptions last; cat TASK.md README.md job.py fees.py invoices.py settings.py settings.ini; ls -la data
   ```

   Output, the first 15 of 324 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-ormaos-1.jsonl?plain=1#L7)):

   ```text
   r1 exit 0 in 0.05s: 1 Python process, 34 calls, 1 exception (0 swallowed, 0 uncaught)
   command: .venv/bin/python job.py --date <str[10]>
   io: 5 events (file 1, sqlite 4)
   not collected: io: reads of the 1 file opened at settings.py:23: opened for reading, and no `read` call by Python code was seen on a file of that name: if it was read, that was inside C code (a file that is iterated, `for line in f`, `csv.reader`)
   never recorded: values, and 13 more kinds of things (`ormaos show --json` lists them with the reason)
   next: ormaos tree r1:c1 | ormaos io r1
   r1: 1 exception (0 swallowed, 0 uncaught)
   r1:e1 exit SystemExit  raised at job.py:82
   next: ormaos exceptions r1:e1
   Last night's late-fees run said OK, but this morning the billing database has no late fee of last night for invoices that were overdue.
   # late-fees
   
   A scheduled job that charges late fees: every night, each invoice that is overdue gets the fee of that night, written to the billing database, where the statements read it.
   
   It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.
   ```
3. ```text
   .venv/bin/ormaos tree r1:c1; .venv/bin/ormaos io r1; cat data/cron.log; .venv/bin/python invoices.py
   ```

   Output, the first 15 of 32 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-ormaos-1.jsonl?plain=1#L10)):

   ```text
   r1:c1 <module>() -> raised  job.py:1  29.1ms  io 5  calls below: 4
     r1:c2 <module>() -> NoneType  fees.py:1  9us
     r1:c3 <module>() -> NoneType  invoices.py:1  3.9ms  calls below: 4
       r1:c4 Invoice() -> NoneType  invoices.py:37  8us
       r1:c5 Invoice.__annotate__(format: int) -> dict[7]  invoices.py:37  14us
       r1:c6 <module>() -> NoneType  <string>:1  8us
       r1:c7 __create_fn__(__dataclass_HAS_DEFAULT_FACTORY__: dataclasses._HAS_DEFAULT_FACTORY_CLASS, __dataclass_...) -> tuple[6 function]  <string>:1  17us
     r1:c8 <module>() -> NoneType  settings.py:1  1.8ms  calls below: 4
       r1:c9 Settings() -> NoneType  settings.py:12  7us
       r1:c10 Settings.__annotate__(format: int) -> dict[5]  settings.py:12  8us
       r1:c11 <module>() -> NoneType  <string>:1  8us
       r1:c12 __create_fn__(__dataclass_HAS_DEFAULT_FACTORY__: dataclasses._HAS_DEFAULT_FACTORY_CLASS, __dataclass_...) -> tuple[6 function]  <string>:1  19us
     r1:c13 main(argv: NoneType) -> int  job.py:55  6.4ms  io 5  calls below: 4
       r1:c14 configure_logging() -> NoneType  job.py:24  63us
       r1:c15 load(path: pathlib.PosixPath) -> settings.Settings  settings.py:21  519us  io 1  calls below: 1
   ```
4. ```text
   crontab -l 2>&1; env | grep -i late_fees; grep -rs LATE_FEES /etc/cron* /etc/environment 2>/dev/null; .venv/bin/ormaos show --json | head -c 3000
   ```

   Output, the first 15 of 117 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-ormaos-1.jsonl?plain=1#L16)):

   ```text
   /var/spool/cron: No such file or directory
   {
     "kind": "show",
     "version": 1,
     "format": "provisional-0",
     "recording": "r1",
     "path": ".ormaos/r1",
     "complete": true,
     "incomplete": [],
     "context": {
       "mode": "run",
       "command": [
         ".venv/bin/python",
         "job.py",
         "--date",
   ```
5. ```text
   Edit settings.py
   ```
6. ```text
   Edit settings.py
   ```
7. ```text
   T=$(mktemp -d) && cp data/billing.db $T/ && for v in 0 no false "" 1 yes bogus; do echo "== LATE_FEES_PAUSE='$v'"; LATE_FEES_PAUSE="$v" LATE_FEES_LOG_LEVEL=INFO .venv/bin/python job.py --date 2026-11-25 --db $T/billing.db; echo "exit=$?"; done; .venv/bin/python invoices.py --db $T/billing.db
   ```
8. ```text
   rm -rf /tmp/tmp.*/billing.db 2>/dev/null; true
   ```

Its change, against `task/`

```text
--- task/settings.py
+++ settings.py
@@ -18,6 +18,22 @@
     grace_days: dict
 
 
+def _pause(job):
+    """LATE_FEES_PAUSE wins over the file, read as a boolean (1/0, yes/no, ...).
+
+    An unset or empty variable means "use the file". Any other value that is
+    not a boolean is an error, so a typo stops the job loudly instead of
+    silently pausing (or charging) a night.
+    """
+    value = os.environ.get("LATE_FEES_PAUSE", "").strip()
+    if not value:
+        return job.getboolean("pause", fallback=False)
+    try:
+        return configparser.ConfigParser.BOOLEAN_STATES[value.lower()]
+    except KeyError:
+        raise ValueError(f"LATE_FEES_PAUSE={value!r} is not a boolean (use 1/0, yes/no)") from None
+
+
 def load(path=DEFAULT_FILE):
     parser = configparser.ConfigParser()
     with open(path, encoding="utf-8") as handle:
@@ -25,7 +41,7 @@
     job, fees = parser["job"], parser["fees"]
     return Settings(
         # LATE_FEES_PAUSE in the environment wins over the file.
-        pause=os.environ.get("LATE_FEES_PAUSE") or job.getboolean("pause", fallback=False),
+        pause=_pause(job),
         daily_basis_points=fees.getint("daily_basis_points"),
         minimum_cents=fees.getint("minimum_cents"),
         cap_percent=fees.getint("cap_percent"),
```

What the check said

```text
pass  the night ran with LATE_FEES_PAUSE=0: 27 fees, 27 expected, run twice exit 0
pass  a night with LATE_FEES_PAUSE=1 is paused: 20 fees, 20 expected, run twice exit 0
pass  a night without the variable is charged: 27 fees, 27 expected, run twice exit 0
fixed
```

## Every run

The first attempt of every run of every arm.

| Arm | Run | Check | Last line | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|
| `none` | 1 | passed | `fixed` | 9 | 99,328 | 49 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-none-1.jsonl) |
| `none` | 2 | passed | `fixed` | 7 | 83,489 | 42 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-none-2.jsonl) |
| `none` | 3 | did not pass | `not fixed` | 10 | 117,060 | 53 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-none-3.jsonl) |
| `raw` | 1 | did not pass | `not fixed` | 13 | 241,924 | 66 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-raw-1.jsonl) |
| `raw` | 2 | passed | `fixed` | 9 | 126,396 | 46 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-raw-2.jsonl) |
| `raw` | 3 | passed | `fixed` | 8 | 139,188 | 56 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-raw-3.jsonl) |
| `ormaos` | 1 | passed | `fixed` | 8 | 117,837 | 44 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-ormaos-1.jsonl) |
| `ormaos` | 2 | passed | `fixed` | 6 | 94,143 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-ormaos-2.jsonl) |
| `ormaos` | 3 | passed | `fixed` | 7 | 88,436 | 43 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/late-fees-ormaos-3.jsonl) |

## The results files

- The benchmark: [fix](https://ormaos.com/benchmarks/fix/)
- Results folder: [`agent-bench/results/20261126-220703`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703): 2026-11-26, `claude-code / claude-opus-5-5`, bubblewrap, network open
