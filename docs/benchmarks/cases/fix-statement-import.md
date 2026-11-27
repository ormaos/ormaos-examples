# statement-import, in fix

*Situation · fix*

A scheduled job. By its README, it books a bank statement into a ledger. Source: [`agent-bench/bugs/statement-import/task`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/bugs/statement-import/task).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Passed the check, first attempts: `none` 3/3, `raw` 3/3, `ormaos` 3/3 (3 runs per arm). Agent: `claude-code / claude-opus-5-5`.

## What happened

That night cron ran `python3 job.py`; it printed `statement import finished: OK` and exited with code 0. This morning the ledger adds up to 2049385 and the bank's closing balance of yesterday is 2072155. Where it behaved otherwise than its README: a loop that stops before the end of its input.

The items are those the scenario's own check of the data found, in [`build.json`](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/build.json).

The symptom, from `TASK.md` in the agent's folder:

```text
Last night's statement import said OK, but this morning the balance of the ledger is not the bank's closing balance of yesterday (data/bank_balance.csv).
```

## What the agent was given

Its folder (the code, its README, `TASK.md` and the data that night left, with what the arm adds) and the task text, the same in every arm but for the arm's last sentence:

`none`:

```text
Last night's statement import said OK, but this morning the balance of the ledger is not the bank's closing balance of yesterday (data/bank_balance.csv). The job runs from cron with `python3 job.py`. Find the cause and fix it.
```

`raw`:

```text
Last night's statement import said OK, but this morning the balance of the ledger is not the bank's closing balance of yesterday (data/bank_balance.csv). The job runs from cron with `python3 job.py`. Find the cause and fix it. A VizTracer trace of that run is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
Last night's statement import said OK, but this morning the balance of the ledger is not the bank's closing balance of yesterday (data/bank_balance.csv). The job runs from cron with `python3 job.py`. Find the cause and fix it. That run was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the first 15 lines of its output, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-none-1.jsonl)
- Passed the check
- 5 tool calls, 71,486 tokens, 33 s

Commands, in order (5):

1. ```text
   ls -la && find . -type f | grep -v __pycache__ | head -50 && cat job.py
   ```
2. ```text
   cat ledger.py statement.py README.md TASK.md; cat data/bank_balance.csv; cat data/cron.log; ls -la inbox data
   ```
3. ```text
   python3 ledger.py --compare data/bank_balance.csv; sqlite3 data/ledger.db "select * from entries order by booked_on, bank_id" 2>/dev/null || python3 -c "
   import sqlite3;c=sqlite3.connect('data/ledger.db')
   for r in c.execute('select * from entries order by booked_on,bank_id'):print(r)"
   ```
4. ```text
   Edit statement.py
   ```
5. ```text
   T=$(mktemp -d) && mkdir $T/inbox && cp /srv/statement-import/data/ledger.db $T/ && cat > $T/inbox/statement-20261126.txt <<'EOF'
   H|ACC-7701|2026-11-26
   T|B-88122|2026-11-25|389.90-|B|Insurance
   # a comment
   
   T|B-90001|2026-11-26|10.00|B|after blank line
      
   T|B-90002|2026-11-26|2.50-|B|after whitespace line
   EOF
   cd /srv/statement-import && STATEMENT_IMPORT_LOG_LEVEL=INFO python3 job.py --inbox $T/inbox --db $T/ledger.db; python3 ledger.py --db $T/ledger.db; rm -r $T
   ```

Its change, against `task/`

```text
--- task/statement.py
+++ statement.py
@@ -66,11 +66,10 @@
     records = []
     with open(path, encoding="utf-8") as handle:
         account, day = parse_header(handle.readline())
-        while True:
-            line = handle.readline().strip()
-            if not line:
-                break
-            if line.startswith("#"):
+        # Read to the end of the file: an empty line is skipped, not the end.
+        for line in handle:
+            line = line.strip()
+            if not line or line.startswith("#"):
                 continue
             records.append(parse_record(line))
     return account, day, records
```

What the check said

```text
pass  a statement in two parts: exit 0, 0 of 32 entries missing
pass  a statement in one part: exit 0, 0 of 32 entries missing
pass  empty lines and a comment at the end: exit 0, 0 of 32 entries missing
pass  a statement of another account is refused: exit 2, 1 file left in the inbox
fixed
```

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-raw-1.jsonl)
- Passed the check
- 6 tool calls, 82,665 tokens, 38 s

Commands, in order (6):

1. ```text
   ls -la && ls -la data && cat job.py && head -50 data/*.csv
   ```
2. ```text
   cat README.md TASK.md ledger.py statement.py data/cron.log; ls -la inbox
   ```
3. ```text
   python3 ledger.py --compare data/bank_balance.csv; python3 -I - <<'EOF'
   import json,collections
   d=json.load(open('result.json'))
   ev=d['traceEvents']
   c=collections.Counter(e.get('name') for e in ev)
   for k,v in c.most_common(40): print(v,k)
   for e in ev:
       n=e.get('name','')
       if any(s in n for s in ('read (','book_file','unlink','parse_header','main (')): print(e['ts'],e.get('dur'),n, e.get('args'))
   EOF
   ```
4. ```text
   python3 -I - <<'EOF'
   import json
   ev=json.load(open('result.json'))['traceEvents']
   r=[e for e in ev if e.get('name','').startswith('read (/srv')][0]
   inner=[e for e in ev if 'ts' in e and r['ts']<=e['ts']<=r['ts']+r['dur'] and e is not r]
   inner.sort(key=lambda e:e['ts'])
   for e in inner: print(e['ts'],e.get('dur'),e['name'])
   EOF
   sqlite3 data/ledger.db "select * from entries order by booked_on desc, bank_id desc limit 20" 2>/dev/null || python3 -c "import sqlite3;[print(r) for r in sqlite3.connect('data/ledger.db').execute('select * from entries order by booked_on desc, bank_id desc limit 20')]"
   ```
5. ```text
   Edit statement.py
   ```
6. ```text
   cd /tmp && rm -rf sitest && mkdir sitest && cp -r /srv/statement-import/*.py sitest/ && mkdir sitest/inbox sitest/data && cd sitest && python3 ledger.py --db data/t.db --create 0 && printf 'H|ACC-7701|2026-11-25\nT|X-1|2026-11-25|10.00|B|a\n# c\n\nT|X-2|2026-11-25|2.50-|B|b\n\nR|X-3|2026-11-25|X-2\nT|X-4|2026-11-25|5.00|P|p\n' > inbox/statement-20261125.txt && python3 job.py --db data/t.db; echo exit=$?; python3 ledger.py --db data/t.db
   ```

Its change, against `task/`

```text
--- task/statement.py
+++ statement.py
@@ -66,11 +66,9 @@
     records = []
     with open(path, encoding="utf-8") as handle:
         account, day = parse_header(handle.readline())
-        while True:
-            line = handle.readline().strip()
-            if not line:
-                break
-            if line.startswith("#"):
+        for line in handle:
+            line = line.strip()
+            if not line or line.startswith("#"):
                 continue
             records.append(parse_record(line))
     return account, day, records
```

What the check said

```text
pass  a statement in two parts: exit 0, 0 of 32 entries missing
pass  a statement in one part: exit 0, 0 of 32 entries missing
pass  empty lines and a comment at the end: exit 0, 0 of 32 entries missing
pass  a statement of another account is refused: exit 2, 1 file left in the inbox
fixed
```

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-ormaos-1.jsonl)
- Passed the check
- 7 tool calls, 126,262 tokens, 44 s

Commands, in order (7):

1. ```text
   .venv/bin/ormaos guide; ls -la; ls -la .ormaos data
   ```

   Output, the first 15 of 76 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-ormaos-1.jsonl?plain=1#L5)):

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
   cat TASK.md README.md job.py ledger.py statement.py data/bank_balance.csv data/cron.log; ls -la inbox; .venv/bin/ormaos show
   ```

   Output, the first 15 of 330 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-ormaos-1.jsonl?plain=1#L7)):

   ````text
   Last night's statement import said OK, but this morning the balance of the ledger is not the bank's closing balance of yesterday (data/bank_balance.csv).
   # statement-import
   
   A scheduled job that books the bank's statements into the ledger of the account: the bank's transfer drops a statement file in `inbox/` every evening, and the job books it at night, so that the ledger shows the bank's closing balance in the morning.
   
   It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.
   
   ## Run it
   
   ```bash
   python3 job.py      # book the statements in inbox/
   python3 ledger.py   # show the balance
   ```
   
   The job prints `statement import finished: OK` and exits with code 0 when every file in `inbox/` is booked. A file that is not a statement of the account, or that has a line the job cannot read, stops it: it prints `statement import failed: ...` on stderr, exits with code 2, books nothing of that file and leaves it in `inbox/`.
   ````
3. ```text
   .venv/bin/ormaos exceptions r1; .venv/bin/ormaos tree r1 --depth 4; .venv/bin/ormaos io r1; .venv/bin/python ledger.py --compare data/bank_balance.csv
   ```

   Output, the first 15 of 50 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-ormaos-1.jsonl?plain=1#L13)):

   ```text
   r1: 1 exception (0 swallowed, 0 uncaught)
   r1:e1 exit SystemExit  raised at job.py:72
   next: ormaos exceptions r1:e1
   r1:c1 <module>() -> raised  job.py:1  29.5ms  io 36  calls below: 3
     r1:c2 <module>() -> NoneType  ledger.py:1  1.5ms
     r1:c3 <module>() -> NoneType  statement.py:1  720us  calls below: 5
       r1:c4 StatementError() -> NoneType  statement.py:18  7us
       r1:c5 Record() -> NoneType  statement.py:22  9us
       r1:c6 Record.__annotate__(format: int) -> dict[7]  statement.py:22  9us
       r1:c7 <module>() -> NoneType  <string>:1  8us
       r1:c8 __create_fn__(__dataclass_HAS_DEFAULT_FACTORY__: dataclasses._HAS_DEFAULT_FACTORY_CLASS, __dataclass_...) -> tuple[6 function]  <string>:1  23us
     r1:c9 main(argv: NoneType) -> int  job.py:50  7.6ms  io 36  calls below: 3
       r1:c10 configure_logging() -> NoneType  job.py:27  66us
       r1:c11 connect(path: pathlib.PosixPath) -> sqlite3.Connection  ledger.py:27  474us  io 2
       r1:c12 book_file(conn: sqlite3.Connection, path: pathlib.PosixPath) -> tuple[2 int]  job.py:36  1.9ms  io 34  calls below: 12
   ```
4. ```text
   .venv/bin/ormaos io r1:i3; .venv/bin/ormaos io r1:i5 --json | head -80; .venv/bin/ormaos tree r1:c12 --offset 4
   ```

   Output, the first 15 of 76 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-ormaos-1.jsonl?plain=1#L34)):

   ```text
   r1:i3 file open inbox/statement-20261125.txt (read)
     caused at   statement.py:67 in read  [r1:c13]
     inside      r1:c1 <module> > r1:c9 main > r1:c12 book_file
   next: ormaos io r1:c13 | ormaos tree r1:c13 | ormaos io r1
   {
     "kind": "io_event",
     "version": 1,
     "recording": "r1",
     "address": "r1:i5",
     "io_kind": "file",
     "op": "read",
     "target": "inbox/statement-20261125.txt",
     "at": {
       "file": "statement.py",
       "line": 70,
   ```
5. ```text
   .venv/bin/python -I -c "
   import sqlite3;c=sqlite3.connect('file:data/ledger.db?mode=ro',uri=True)
   for r in c.execute('select * from entries order by booked_on, bank_id'):print(r)"
   ```
6. ```text
   Edit statement.py
   ```
7. ```text
   mkdir -p /tmp/sitest/inbox && cd /tmp/sitest && cp /srv/statement-import/data/ledger.db t.db && printf 'H|ACC-7701|2026-11-25\nT|X-1|2026-11-25|1.00|B|a\n\n# c\nT|X-2|2026-11-25|2.50-|B|b\n\n' > inbox/statement-20261125.txt && cd /srv/statement-import && .venv/bin/python job.py --inbox /tmp/sitest/inbox --db /tmp/sitest/t.db; .venv/bin/python -I -c "
   import sqlite3;c=sqlite3.connect('/tmp/sitest/t.db');print(c.execute(\"select * from entries where bank_id like 'X-%'\").fetchall())"; rm -rf /tmp/sitest
   ```

Its change, against `task/`

```text
--- task/statement.py
+++ statement.py
@@ -66,11 +66,11 @@
     records = []
     with open(path, encoding="utf-8") as handle:
         account, day = parse_header(handle.readline())
-        while True:
-            line = handle.readline().strip()
-            if not line:
-                break
-            if line.startswith("#"):
+        # Read to the end of the file: an empty line is skipped, not the end
+        # of the statement (stopping there dropped the records after it).
+        for line in handle:
+            line = line.strip()
+            if not line or line.startswith("#"):
                 continue
             records.append(parse_record(line))
     return account, day, records
```

What the check said

```text
pass  a statement in two parts: exit 0, 0 of 32 entries missing
pass  a statement in one part: exit 0, 0 of 32 entries missing
pass  empty lines and a comment at the end: exit 0, 0 of 32 entries missing
pass  a statement of another account is refused: exit 2, 1 file left in the inbox
fixed
```

## Every run

The first attempt of every run of every arm.

| Arm | Run | Check | Last line | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|
| `none` | 1 | passed | `fixed` | 5 | 71,486 | 33 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-none-1.jsonl) |
| `none` | 2 | passed | `fixed` | 5 | 57,605 | 30 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-none-2.jsonl) |
| `none` | 3 | passed | `fixed` | 5 | 71,802 | 34 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-none-3.jsonl) |
| `raw` | 1 | passed | `fixed` | 6 | 82,665 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-raw-1.jsonl) |
| `raw` | 2 | passed | `fixed` | 8 | 139,037 | 52 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-raw-2.jsonl) |
| `raw` | 3 | passed | `fixed` | 9 | 168,806 | 54 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-raw-3.jsonl) |
| `ormaos` | 1 | passed | `fixed` | 7 | 126,262 | 44 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-ormaos-1.jsonl) |
| `ormaos` | 2 | passed | `fixed` | 7 | 107,515 | 41 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-ormaos-2.jsonl) |
| `ormaos` | 3 | passed | `fixed` | 7 | 128,645 | 46 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/statement-import-ormaos-3.jsonl) |

## The results files

- The benchmark: [fix](https://ormaos.com/benchmarks/fix/)
- Results folder: [`agent-bench/results/20261126-220703`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703)
