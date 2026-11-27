# commission-run, in fix

*Situation · fix*

A scheduled job. By its README, it works out sales commissions. Source: [`agent-bench/bugs/commission-run/task`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/bugs/commission-run/task).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Passed the check, first attempts: `none` 3/3, `raw` 3/3, `ormaos` 3/3 (3 runs per arm). Agent: `claude-code / claude-opus-5-5`.

## What happened

That night cron ran `python3 job.py`; it printed `commissions finished: OK` and exited with code 0. This morning the payouts of 4 reps for yesterday are not what finance worked out: `R-12`, `R-13`, `R-15` and `R-17`. Where it behaved otherwise than its README: a value kept from one item to the next.

The items are those the scenario's own check of the data found, in [`build.json`](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/build.json).

The symptom, from `TASK.md` in the agent's folder:

```text
Last night's commission run said OK, but this morning the payouts of some reps for yesterday are not what finance worked out (data/finance_check.csv).
```

## What the agent was given

Its folder (the code, its README, `TASK.md` and the data that night left, with what the arm adds) and the task text, the same in every arm but for the arm's last sentence:

`none`:

```text
Last night's commission run said OK, but this morning the payouts of some reps for yesterday are not what finance worked out (data/finance_check.csv). The job runs from cron with `python3 job.py`. Find the cause and fix it.
```

`raw`:

```text
Last night's commission run said OK, but this morning the payouts of some reps for yesterday are not what finance worked out (data/finance_check.csv). The job runs from cron with `python3 job.py`. Find the cause and fix it. A VizTracer trace of that run is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
Last night's commission run said OK, but this morning the payouts of some reps for yesterday are not what finance worked out (data/finance_check.csv). The job runs from cron with `python3 job.py`. Find the cause and fix it. That run was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the first 15 lines of its output, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-none-1.jsonl)
- Passed the check
- 5 tool calls, 74,266 tokens, 36 s

Commands, in order (5):

1. ```text
   ls -laR | head -50 && cat job.py
   ```
2. ```text
   cat README.md TASK.md deals.py payouts.py rates.py data/cron.log data/finance_check.csv
   ```
3. ```text
   python3 payouts.py --compare data/finance_check.csv; python3 payouts.py; sqlite3 data/commissions.db "select * from rate_table; select * from reps;" 2>/dev/null || python3 -c "
   import sqlite3;c=sqlite3.connect('data/commissions.db')
   for t in ['rate_table','reps']: print(t, c.execute(f'select * from {t}').fetchall())"
   ```
4. ```text
   python3 - <<'EOF'
   import re
   p='rates.py'; s=open(p).read()
   s=s.replace('''    if rep_id not in _looked_up:''','''    key = (rep_id, product_line)
       if key not in _looked_up:''')
   s=s.replace('''        _looked_up[rep_id] = row[0]
       return _looked_up[rep_id]''','''        _looked_up[key] = row[0]
       return _looked_up[key]''')
   s=s.replace('# The quarter-end run has tens of thousands of deals: a rate is read once a run.',
    '# The quarter-end run has tens of thousands of deals: a rate is read once a run.\n# Keyed by (rep, product line): a rep can have different rates per line.')
   open(p,'w').write(s)
   EOF
   ```

   … 1 more line of this command
5. ```text
   T=$(mktemp -d) && cp data/commissions.db $T/ && mkdir $T/inbox && cat > $T/inbox/deals-20260125.csv <<'EOF'
   deal_id,rep,product_line,amount_cents,status
   D1,R-12,hardware,100000,won
   D2,R-12,software,100000,won
   D3,R-15,hardware,100000,won
   D4,R-15,software,100000,won
   EOF
   python3 job.py --inbox $T/inbox --db $T/commissions.db --date 2099-01-01 && python3 -c "
   import sqlite3;print(sqlite3.connect('$T/commissions.db').execute(\"select * from payouts where day='2099-01-01'\").fetchall())"; rm -rf $T
   ```

Its change, against `task/`

```text
--- task/rates.py
+++ rates.py
@@ -9,12 +9,14 @@
 BIG_DEAL_EXTRA_BP = 50
 
 # The quarter-end run has tens of thousands of deals: a rate is read once a run.
+# Keyed by (rep, product line): a rep can have different rates per line.
 _looked_up = {}
 
 
 def rate_bp(conn, rep_id, product_line):
     """The rate of a rep for a product line, in basis points."""
-    if rep_id not in _looked_up:
+    key = (rep_id, product_line)
+    if key not in _looked_up:
         row = conn.execute(
             "SELECT rate_bp FROM rate_table WHERE rep_id = ? AND product_line = ?",
             (rep_id, product_line),
@@ -26,8 +28,8 @@
             ).fetchone()
         if row is None:
             raise KeyError(f"no rate for product line {product_line!r}")
-        _looked_up[rep_id] = row[0]
-    return _looked_up[rep_id]
+        _looked_up[key] = row[0]
+    return _looked_up[key]
 
 
 def commission_cents(conn, deal, rep_id):
```

What the check said

```text
pass  reps sell in two product lines: exit 0, payouts not as expected: none
pass  every rep sells in one product line: exit 0, payouts not as expected: none
fixed
```

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-raw-1.jsonl)
- Passed the check
- 10 tool calls, 167,382 tokens, 58 s

Commands, in order (10):

1. ```text
   cd /srv/commission-run; ls -la; ls data; cat job.py; head data/finance_check.csv
   ```
2. ```text
   cd /srv/commission-run; cat README.md TASK.md deals.py payouts.py rates.py; cat data/cron.log; ls inbox; cat data/finance_check.csv | wc -l
   ```
3. ```text
   cd /srv/commission-run; ls -la inbox; python3 payouts.py --compare data/finance_check.csv; sqlite3 data/commissions.db "select * from rate_table; select * from reps;" 2>/dev/null || python3 -c "
   import sqlite3;c=sqlite3.connect('data/commissions.db');print(c.execute('select * from rate_table').fetchall());print(c.execute('select * from reps').fetchall())"
   ```
4. ```text
   cd /srv/commission-run; mkdir -p /tmp/ana; cat > /tmp/ana/t.py <<'EOF'
   import json,collections,sys
   d=json.load(open(sys.argv[1]))
   ev=d["traceEvents"]
   print(len(ev), d.keys())
   c=collections.Counter(e.get("name") for e in ev)
   for k,v in c.most_common(60): print(v,k)
   print([e for e in ev if "args" in e][:5])
   EOF
   python3 -I /tmp/ana/t.py result.json
   ```
5. ```text
   cd /srv/commission-run; cat > /tmp/ana/t2.py <<'EOF'
   import json,sys
   d=json.load(open(sys.argv[1]))
   ev=sorted([e for e in d["traceEvents"] if e.get("ph")=="X"],key=lambda e:e["ts"])
   keep=("commission-run","sqlite3","Connection","Cursor","unlink","glob","print","write","exit","Deal.","fetch")
   for e in ev:
       n=e["name"]
       if any(k in n for k in keep) and "importlib" not in n:
           print(round(e["ts"]), round(e["dur"]), n)
   EOF
   python3 -I /tmp/ana/t2.py result.json | head -150
   ```
6. ```text
   cd /srv/commission-run; python3 -I /tmp/ana/t2.py result.json | sed -n '150,400p' | grep -v RLock
   ```
7. ```text
   Edit rates.py
   ```
8. ```text
   Edit rates.py
   ```
9. ```text
   cd /tmp/ana && rm -rf t && mkdir -p t/inbox && cp /srv/commission-run/data/commissions.db t/ && cat > t/inbox/deals-20261125.csv <<'EOF'
   deal_id,rep,product_line,amount_cents,status
   D1,R-12,software,100000,won
   D2,R-12,hardware,100000,won
   D3,R-12+R-15,hardware,2000000,won
   D4,R-17,services,100000,won
   D5,R-17,software,100000,won
   EOF
   cd /srv/commission-run && python3 job.py --inbox /tmp/ana/t/inbox --db /tmp/ana/t/commissions.db --date 2030-01-01; python3 payouts.py --db /tmp/ana/t/commissions.db | grep 2030
   ```
10. ```text
   find / -name 'deals-2026112*' 2>/dev/null; ls /srv/commission-run/data
   ```

Its change, against `task/`

```text
--- task/rates.py
+++ rates.py
@@ -14,7 +14,9 @@
 
 def rate_bp(conn, rep_id, product_line):
     """The rate of a rep for a product line, in basis points."""
-    if rep_id not in _looked_up:
+    # The rate depends on the rep *and* the product line: cache on both.
+    key = (rep_id, product_line)
+    if key not in _looked_up:
         row = conn.execute(
             "SELECT rate_bp FROM rate_table WHERE rep_id = ? AND product_line = ?",
             (rep_id, product_line),
@@ -26,8 +28,8 @@
             ).fetchone()
         if row is None:
             raise KeyError(f"no rate for product line {product_line!r}")
-        _looked_up[rep_id] = row[0]
-    return _looked_up[rep_id]
+        _looked_up[key] = row[0]
+    return _looked_up[key]
 
 
 def commission_cents(conn, deal, rep_id):
```

What the check said

```text
pass  reps sell in two product lines: exit 0, payouts not as expected: none
pass  every rep sells in one product line: exit 0, payouts not as expected: none
fixed
```

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-ormaos-1.jsonl)
- Passed the check
- 5 tool calls, 88,453 tokens, 34 s

Commands, in order (5):

1. ```text
   .venv/bin/ormaos guide; ls -la; ls -la .ormaos data
   ```

   Output, the first 15 of 77 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-ormaos-1.jsonl?plain=1#L5)):

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
   cat README.md TASK.md job.py deals.py payouts.py rates.py data/cron.log data/finance_check.csv; ls -la inbox; .venv/bin/ormaos show
   ```

   Output, the first 15 of 336 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-ormaos-1.jsonl?plain=1#L7)):

   ````text
   # commission-run
   
   A scheduled job that works out sales commissions: the CRM's export drops the day's deals in `inbox/` every evening, and at night the job writes each rep's commission on them to a database, where payroll reads it.
   
   It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.
   
   ## Run it
   
   ```bash
   python3 job.py       # work out the deals in inbox/
   python3 payouts.py   # show the payouts, per day
   ```
   
   The job prints `commissions finished: OK` and exits with code 0 when every file in `inbox/` was handled. If it cannot run (no database, a product line without a rate), it prints `commissions failed: ...` on stderr and exits with code 2.
   
   ````
3. ```text
   .venv/bin/ormaos io r1; .venv/bin/ormaos tree r1:c1 --depth 3; python3 payouts.py --compare data/finance_check.csv; sqlite3 data/commissions.db "select * from rate_table order by 1,2; select * from reps;" 2>&1 || python3 -c "
   import sqlite3;c=sqlite3.connect('data/commissions.db')
   print(c.execute('select * from rate_table order by 1,2').fetchall());print(c.execute('select * from reps').fetchall())"
   ```

   Output, the first 15 of 66 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-ormaos-1.jsonl?plain=1#L11)):

   ```text
   r1: 31 io events (sqlite 30, file 1)
     1x sqlite connect data/commissions.db  at payouts.py:39 in connect  [r1:i1]
     1x sqlite CREATE TABLE IF NOT EXISTS reps ( rep_id TEXT PRIMARY KEY, name TEXT ...  at payouts.py:40 in connect  [r1:i2]
     1x sqlite CREATE TABLE IF NOT EXISTS rate_table ( rep_id TEXT NOT NULL, product...  at payouts.py:40 in connect  [r1:i3]
     1x sqlite CREATE TABLE IF NOT EXISTS payouts ( day TEXT NOT NULL, rep_id TEXT N...  at payouts.py:40 in connect  [r1:i4]
     1x file open inbox/deals-20261125.csv (read)  at deals.py:27 in read  [r1:i5]
     1x sqlite SELECT rep_id FROM reps  at payouts.py:45 in known_reps  [r1:i6]
     8x sqlite SELECT rate_bp FROM rate_table WHERE rep_id = ? AND product_line = ?  at rates.py:18 in rate_bp  [r1:i7]
     6x sqlite SELECT rate_bp FROM rate_table WHERE rep_id = ? AND product_line = ?  at rates.py:23 in rate_bp  [r1:i8]
     1x sqlite BEGIN  at payouts.py:51 in write_day  [r1:i21]
     1x sqlite DELETE FROM payouts WHERE day = ?  at payouts.py:51 in write_day  [r1:i22]
     8x sqlite INSERT INTO payouts (day, rep_id, deals, commission_cents) VALUES (?,...  at payouts.py:52 in write_day  [r1:i23]
     1x sqlite COMMIT  at payouts.py:50 in write_day  [r1:i24]
   next: ormaos io r1:i1 | ormaos io r1:i2 | ormaos io r1:c11 | ormaos exceptions r1
   r1:c1 <module>() -> raised  job.py:1  30.4ms  io 31  calls below: 4
   ```
4. ```text
   python3 - <<'EOF'
   p='rates.py'; s=open(p).read()
   s=s.replace("""    if rep_id not in _looked_up:""","""    key = (rep_id, product_line)
       if key not in _looked_up:""")
   s=s.replace("""        _looked_up[rep_id] = row[0]
       return _looked_up[rep_id]""","""        _looked_up[key] = row[0]
       return _looked_up[key]""")
   open(p,'w').write(s)
   EOF
   sed -n 13,35p rates.py
   mkdir -p /tmp/crtest && cp data/commissions.db /tmp/crtest/t.db && cd /tmp/crtest && mkdir -p in && cat > in/deals-20261125.csv <<'EOF'
   deal_id,rep,product_line,amount_cents,status
   ```

   … 7 more lines of this command
5. ```text
   rm -rf /tmp/crtest
   ```

Its change, against `task/`

```text
--- task/rates.py
+++ rates.py
@@ -14,7 +14,8 @@
 
 def rate_bp(conn, rep_id, product_line):
     """The rate of a rep for a product line, in basis points."""
-    if rep_id not in _looked_up:
+    key = (rep_id, product_line)
+    if key not in _looked_up:
         row = conn.execute(
             "SELECT rate_bp FROM rate_table WHERE rep_id = ? AND product_line = ?",
             (rep_id, product_line),
@@ -26,8 +27,8 @@
             ).fetchone()
         if row is None:
             raise KeyError(f"no rate for product line {product_line!r}")
-        _looked_up[rep_id] = row[0]
-    return _looked_up[rep_id]
+        _looked_up[key] = row[0]
+    return _looked_up[key]
 
 
 def commission_cents(conn, deal, rep_id):
```

What the check said

```text
pass  reps sell in two product lines: exit 0, payouts not as expected: none
pass  every rep sells in one product line: exit 0, payouts not as expected: none
fixed
```

## Every run

The first attempt of every run of every arm.

| Arm | Run | Check | Last line | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|
| `none` | 1 | passed | `fixed` | 5 | 74,266 | 36 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-none-1.jsonl) |
| `none` | 2 | passed | `fixed` | 6 | 97,309 | 49 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-none-2.jsonl) |
| `none` | 3 | passed | `fixed` | 6 | 75,645 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-none-3.jsonl) |
| `raw` | 1 | passed | `fixed` | 10 | 167,382 | 58 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-raw-1.jsonl) |
| `raw` | 2 | passed | `fixed` | 7 | 117,610 | 44 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-raw-2.jsonl) |
| `raw` | 3 | passed | `fixed` | 5 | 87,995 | 39 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-raw-3.jsonl) |
| `ormaos` | 1 | passed | `fixed` | 5 | 88,453 | 34 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-ormaos-1.jsonl) |
| `ormaos` | 2 | passed | `fixed` | 7 | 85,815 | 34 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-ormaos-2.jsonl) |
| `ormaos` | 3 | passed | `fixed` | 6 | 96,978 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/commission-run-ormaos-3.jsonl) |

## The results files

- The benchmark: [fix](https://ormaos.com/benchmarks/fix/)
- Results folder: [`agent-bench/results/20261126-220703`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703)
