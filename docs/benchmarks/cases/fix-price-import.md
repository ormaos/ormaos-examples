# price-import, in fix

*Situation · fix*

A scheduled job. By its README, it takes over a supplier's price list. Source: [`agent-bench/bugs/price-import/task`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/bugs/price-import/task).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Passed the check, first attempts:

- 2026-11-26, `claude-code / claude-opus-5-5`, bubblewrap, network open: `none` 3/3, `raw` 3/3, `ormaos` 3/3 (3 runs per arm)

## What happened

That night cron ran `python3 job.py`; it printed `price import finished: OK` and exited with code 0. This morning 11 prices in the catalog are not those of the supplier's list: `ART-2110`, `ART-2112`, `ART-2114`, `ART-2115`, `ART-2116`, `ART-2117`, `ART-2120`, `ART-2121`, `ART-2122`, `ART-2124` and `ART-2125`. Where it behaved otherwise than its README: a subprocess whose exit code is not read.

The items are those the scenario's own check of the data found, in [`build.json`](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/build.json).

The symptom, from `TASK.md` in the agent's folder:

```text
Last night's price import said OK, but this morning many prices in the catalog are not the prices of the supplier's list (data/supplier/pricelist.csv).
```

## What the agent was given

Its folder (the code, its README, `TASK.md` and the data that night left, with what the arm adds) and the task text, the same in every arm but for the arm's last sentence:

`none`:

```text
Last night's price import said OK, but this morning many prices in the catalog are not the prices of the supplier's list (data/supplier/pricelist.csv). The job runs from cron with `python3 job.py`. Find the cause and fix it.
```

`raw`:

```text
Last night's price import said OK, but this morning many prices in the catalog are not the prices of the supplier's list (data/supplier/pricelist.csv). The job runs from cron with `python3 job.py`. Find the cause and fix it. A VizTracer trace of that run is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
Last night's price import said OK, but this morning many prices in the catalog are not the prices of the supplier's list (data/supplier/pricelist.csv). The job runs from cron with `python3 job.py`. Find the cause and fix it. That run was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the first 15 lines of its output, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-none-1.jsonl)
- Passed the check
- 9 tool calls, 130,217 tokens, 59 s

Commands, in order (9):

1. ```text
   ls -laR | head -50 && cat job.py
   ```
2. ```text
   cat convert.py catalog.py README.md TASK.md data/cron.log data/staging.csv; echo ---; cat data/supplier/pricelist.csv; echo ---; ls -l --time-style=full-iso data data/supplier
   ```
3. ```text
   python3 convert.py data/supplier/pricelist.csv /tmp/conv.csv; echo exit=$?; cat /tmp/conv.csv; python3 catalog.py --compare data/supplier/pricelist.csv
   ```
4. ```text
   cd /tmp && mkdir -p trunc && head -c 420 /srv/price-import/data/supplier/pricelist.csv > trunc/list.csv && tail -2 trunc/list.csv; echo; python3 /srv/price-import/convert.py trunc/list.csv trunc/out.csv; echo exit=$?; wc -l trunc/out.csv
   ```
5. ```text
   Edit job.py
   ```
6. ```text
   Edit job.py
   ```
7. ```text
   T=$(mktemp -d) && cp data/catalog.db $T/db && python3 job.py --list /tmp/trunc/list.csv --staging $T/s.csv --db $T/db; echo exit=$?; printf 'article;description;price;currency;pack\nART-2101;x;18,90;EUR;100\nAR' > $T/nonl.csv; python3 job.py --list $T/nonl.csv --staging $T/s.csv --db $T/db; echo exit=$?; python3 catalog.py --db $T/db --compare data/supplier/pricelist.csv | wc -l; python3 job.py --staging $T/s.csv --db $T/db; echo exit=$?; python3 catalog.py --db $T/db --compare data/supplier/pricelist.csv; ls $T
   ```
8. ```text
   T=$(mktemp -d) && cp data/catalog.db $T/db && printf 'article;description;price;currency;pack\nART-2101;x;18,90;EUR;100\nART-2102;x;abc;EUR;1\n' > $T/bad.csv && python3 job.py --list $T/bad.csv --staging $T/s.csv --db $T/db; echo exit=$?; ls $T
   ```
9. ```text
   cp -p data/catalog.db data/catalog.db.bak-2026-11-26 && python3 job.py; echo exit=$?; python3 catalog.py --compare data/supplier/pricelist.csv; wc -l data/staging.csv
   ```

Its change, against `task/`

```text
--- task/job.py
+++ job.py
@@ -34,12 +34,55 @@
     )
 
 
+def snapshot_list(supplier_list, target):
+    """Copy the supplier's list, making sure the sync did not change it meanwhile.
+
+    The supplier's sync can replace the list at any time; reading it while it
+    is being written gives a cut-off list.
+    """
+    supplier_list = Path(supplier_list)
+    before = supplier_list.stat()
+    data = supplier_list.read_bytes()
+    after = supplier_list.stat()
+    same = (before.st_ino, before.st_size, before.st_mtime_ns) == (
+        after.st_ino, after.st_size, after.st_mtime_ns)
+    if not same or len(data) != after.st_size:
+        raise ValueError(f"{supplier_list} changed while it was read; run again")
+    if not data.endswith(b"\n"):
+        raise ValueError(f"{supplier_list} does not end with a newline; it looks cut off")
+    Path(target).write_bytes(data)
+
+
 def convert_list(supplier_list, staging):
     """Run the converter, a program of its own that purchasing also uses by hand."""
     command = [sys.executable, str(HERE / "convert.py"), str(supplier_list), str(staging)]
     log.info("running %s", " ".join(command))
-    # The converter reports its progress line by line; keep that out of cron's mail.
-    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
+    # The converter reports its progress line by line; keep that out of cron's mail,
+    # but keep it to tell what went wrong if it fails.
+    result = subprocess.run(command, capture_output=True, text=True)
+    if result.returncode != 0:
+        detail = (result.stderr or result.stdout).strip().splitlines()
+        raise ValueError(
+            f"converter exited with {result.returncode}: "
+            f"{detail[-1] if detail else 'no output'}"
+        )
+
+
+def convert_and_load(conn, supplier_list, staging):
+    """Convert a snapshot of the list to a fresh file, load it, then keep it as staging."""
+    staging = Path(staging)
+    snapshot = staging.with_name(staging.name + ".list.tmp")
+    fresh = staging.with_name(staging.name + ".tmp")
+    try:
+        snapshot_list(supplier_list, snapshot)
+        fresh.unlink(missing_ok=True)
+        convert_list(snapshot, fresh)
+        rows = catalog.load(conn, fresh)
+        os.replace(fresh, staging)
+        return rows
+    finally:
+        snapshot.unlink(missing_ok=True)
+        fresh.unlink(missing_ok=True)
 
 
 def main(argv=None):
@@ -52,8 +95,7 @@
 
     try:
         conn = catalog.connect(args.db)
-        convert_list(args.list, args.staging)
-        rows = catalog.load(conn, args.staging)
+        rows = convert_and_load(conn, args.list, args.staging)
     except (OSError, ValueError, KeyError) as exc:
         print(f"price import failed: {exc}", file=sys.stderr)
         return 2
```

What the check said

```text
pass  a list with a price that is not a number: exit 2, 14 products not at the list's price
pass  a list of prices only: exit 0, not as expected: none
pass  a list without the price column: exit 2, catalog changed: no
fixed
```

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-raw-1.jsonl)
- Passed the check
- 9 tool calls, 163,401 tokens, 60 s

Commands, in order (9):

1. ```text
   ls -la && find . -type f -not -path './.git/*' | head -50 && cat job.py
   ```
2. ```text
   cat convert.py catalog.py README.md TASK.md data/cron.log; head -5 data/supplier/pricelist.csv data/staging.csv; wc -l data/supplier/pricelist.csv data/staging.csv; ls -la --time-style=full-iso data data/supplier
   ```
3. ```text
   cat -A data/supplier/pricelist.csv; cat data/staging.csv; python3 -c "
   import json
   d=json.load(open('result.json'))
   ev=d['traceEvents']
   print(len(ev), set(e.get('ph') for e in ev))
   names={}
   for e in ev: names[e.get('name')]=names.get(e.get('name'),0)+1
   for n,c in sorted(names.items(),key=lambda x:-x[1])[:60]: print(c,n)
   print([k for k in d if k!='traceEvents'])
   "
   ```
4. ```text
   python3 -c "
   import json
   d=json.load(open('result.json'))
   print(json.dumps(d['viztracer_metadata'])[:500])
   ev=d['traceEvents']
   import collections
   print(collections.Counter((e.get('pid'),e.get('tid')) for e in ev))
   for e in ev:
     if e.get('ph')=='M': print(e)
   keys=('convert','catalog','job.py','subprocess','Popen','wait','communicate','piece_cents','to_cents','load','open','main','Decimal','DictReader.__next__','writerow','print','exit')
   for e in sorted(ev,key=lambda e:e.get('ts',0)):
     n=e.get('name','')
   ```

   … 3 more lines of this command
5. ```text
   python3 -c "
   import json
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('pid')==3 and e.get('ph')=='X']
   ev.sort(key=lambda e:e['ts'])
   for e in ev:
     n=e['name']
     if 'importlib' in n or '_bootstrap' in n or 'RLock' in n or 're/_' in n: continue
     print(round(e['ts']),e.get('dur'),n,e.get('args',''))
   " | grep -v -E 'marshal|open_code|BufferedReader' | tail -120
   ```
6. ```text
   python3 catalog.py --compare data/supplier/pricelist.csv; mkdir -p /tmp/pi && python3 convert.py data/supplier/pricelist.csv /tmp/pi/c.csv; echo rc=$?
   ```
7. ```text
   Edit job.py
   ```
8. ```text
   mkdir -p /tmp/pi/t && printf 'article;description;price;currency;pack\nART-1;x;1,00;EUR;1\nART-2;y;abc;EUR;1\n' > /tmp/pi/t/bad.csv && cp data/catalog.db /tmp/pi/t/db && python3 job.py --list /tmp/pi/t/bad.csv --staging /tmp/pi/t/s.csv --db /tmp/pi/t/db; echo rc=$?
   ```
9. ```text
   cp -p data/catalog.db /tmp/pi/catalog.db.before-rerun && python3 job.py; echo rc=$?; python3 catalog.py --compare data/supplier/pricelist.csv; wc -l data/staging.csv
   ```

Its change, against `task/`

```text
--- task/job.py
+++ job.py
@@ -38,8 +38,15 @@
     """Run the converter, a program of its own that purchasing also uses by hand."""
     command = [sys.executable, str(HERE / "convert.py"), str(supplier_list), str(staging)]
     log.info("running %s", " ".join(command))
-    # The converter reports its progress line by line; keep that out of cron's mail.
-    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
+    # The converter reports its progress line by line; keep that out of cron's mail,
+    # but keep its errors: if it fails, the staging file is partial or stale and
+    # must not be loaded.
+    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
+    if result.returncode != 0:
+        lines = result.stderr.strip().splitlines()
+        reason = lines[-1] if lines else "no error output"
+        log.error("converter output:\n%s", result.stderr)
+        raise ValueError(f"converter exited with code {result.returncode}: {reason}")
 
 
 def main(argv=None):
```

What the check said

```text
pass  a list with a price that is not a number: exit 2, 14 products not at the list's price
pass  a list of prices only: exit 0, not as expected: none
pass  a list without the price column: exit 2, catalog changed: no
fixed
```

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-ormaos-1.jsonl)
- Passed the check
- 11 tool calls, 175,219 tokens, 66 s

Commands, in order (11):

1. ```text
   .venv/bin/ormaos guide; ls -la; ls -la .ormaos data data/*
   ```

   Output, the first 15 of 86 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-ormaos-1.jsonl?plain=1#L5)):

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
   cat TASK.md README.md job.py convert.py catalog.py data/cron.log data/staging.csv data/supplier/pricelist.csv; .venv/bin/ormaos show
   ```

   Output, the first 15 of 329 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-ormaos-1.jsonl?plain=1#L7)):

   ````text
   Last night's price import said OK, but this morning many prices in the catalog are not the prices of the supplier's list (data/supplier/pricelist.csv).
   # price-import
   
   A scheduled job that takes over the supplier's price list: the supplier's sync writes the current list to `data/supplier/pricelist.csv`, and at night the job converts it and writes its prices to the catalog, where the shop reads them in the morning.
   
   It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.
   
   ## Run it
   
   ```bash
   python3 job.py                                           # take over the prices
   python3 catalog.py                                       # show the catalog
   python3 catalog.py --compare data/supplier/pricelist.csv # catalog prices that are not the list's
   ```
   
   ````
3. ```text
   .venv/bin/ormaos exceptions r1:e3; .venv/bin/ormaos tree r1:c1; .venv/bin/ormaos io r1; .venv/bin/python catalog.py --compare data/supplier/pricelist.csv; .venv/bin/python catalog.py
   ```

   Output, the first 15 of 63 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-ormaos-1.jsonl?plain=1#L13)):

   ```text
   r1:e3 decimal.InvalidOperation: uncaught
     raised at   convert.py:22 in to_cents  [r1:c28]
     left calls   to_cents [r1:c28], convert [r1:c11], main [r1:c10], <module> [r1:c9]
     handled at  nowhere seen
     message     not recorded; args: tuple[1 list]
   next: ormaos tree r1:c28
   r1:c1 <module>() -> raised  job.py:1  69.3ms  io 23  calls below: 2
     r1:c2 <module>() -> NoneType  catalog.py:1  2.4ms  calls below: 1
       r1:c3 <module>() -> NoneType  convert.py:1  841us
     r1:c4 main(argv: NoneType) -> int  job.py:45  45.7ms  io 23  calls below: 4
       r1:c5 configure_logging() -> NoneType  job.py:28  66us
       r1:c6 connect(path: pathlib.PosixPath) -> sqlite3.Connection  catalog.py:29  452us  io 2
       r1:c7 convert_list(supplier_list: pathlib.PosixPath, staging: pathlib.PosixPath) -> NoneType  job.py:37  39.5ms  io 2
       r1:c8 load(conn: sqlite3.Connection, staging: pathlib.PosixPath) -> int  catalog.py:35  1.6ms  io 19
   next: ormaos exceptions r1:c1
   ```
4. ```text
   .venv/bin/ormaos tree r1:c28; .venv/bin/ormaos tree r1:c11; .venv/bin/python convert.py data/supplier/pricelist.csv /tmp/conv.csv; echo exit=$?; cat /tmp/conv.csv | head -12
   ```

   Output, the first 15 of 39 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-ormaos-1.jsonl?plain=1#L20)):

   ```text
   inside: r1:c9 <module> > r1:c10 main > r1:c11 convert
   r1:c28 to_cents(text: str[10]) -> raised  convert.py:19  27us  process 2
   next: ormaos tree r1:c11 | ormaos exceptions r1:c28
   inside: r1:c9 <module> > r1:c10 main
   r1:c11 convert(source: str[45], target: str[34]) -> raised  convert.py:31  1.0ms  io 2  process 2  calls below: 17
     r1:c12 to_cents(text: str[5]) -> int  convert.py:19  25us  process 2
     r1:c13 piece_cents(pack_cents: int, pack: str[3]) -> int  convert.py:25  14us  process 2
     r1:c14 to_cents(text: str[4]) -> int  convert.py:19  8us  process 2
     r1:c15 piece_cents(pack_cents: int, pack: str[3]) -> int  convert.py:25  8us  process 2
     r1:c16 to_cents(text: str[4]) -> int  convert.py:19  7us  process 2
     r1:c17 piece_cents(pack_cents: int, pack: str[3]) -> int  convert.py:25  7us  process 2
     r1:c18 to_cents(text: str[5]) -> int  convert.py:19  8us  process 2
     r1:c19 piece_cents(pack_cents: int, pack: str[3]) -> int  convert.py:25  7us  process 2
     r1:c20 to_cents(text: str[4]) -> int  convert.py:19  6us  process 2
     r1:c21 piece_cents(pack_cents: int, pack: str[3]) -> int  convert.py:25  7us  process 2
   ```
5. ```text
   .venv/bin/ormaos exceptions r1
   ```

   Output, all 5 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-ormaos-1.jsonl?plain=1#L29)):

   ```text
   r1: 3 exceptions (0 swallowed, 1 uncaught, 1 StopIteration taken by the interpreter)
   r1:e3 uncaught decimal.InvalidOperation  raised at convert.py:22  process 2
   r1:e2 exit SystemExit  raised at job.py:67
   1x StopIteration taken by the interpreter, at /usr/lib/python3.14/csv.py:177 in DictReader.__next__  [r1:e1]
   next: ormaos exceptions r1:e3 | ormaos exceptions r1:e2
   ```
6. ```text
   Edit job.py
   ```
7. ```text
   Edit convert.py
   ```
8. ```text
   Edit convert.py
   ```
9. ```text
   Edit convert.py
   ```
10. ```text
   T=$(mktemp -d) && cp data/catalog.db $T/db && cp data/staging.csv $T/staging.csv && sed 's/^ART-2109;Angle bracket 60 mm;24,00/ART-2109;Angle bracket 60 mm;24,00 EUR/' data/supplier/pricelist.csv > $T/bad.csv
   echo "--- bad list"; .venv/bin/python job.py --list $T/bad.csv --staging $T/staging.csv --db $T/db; echo exit=$?; ls $T; cmp $T/db data/catalog.db && echo "db untouched"; cmp $T/staging.csv data/staging.csv && echo "staging untouched"
   echo "--- real list"; .venv/bin/python job.py --staging $T/staging.csv --db $T/db; echo exit=$?; .venv/bin/python catalog.py --db $T/db --compare data/supplier/pricelist.csv
   ```
11. ```text
   cp -p data/catalog.db data/catalog.db.bak-2026-11-26 && .venv/bin/python job.py; echo exit=$?; .venv/bin/python catalog.py --compare data/supplier/pricelist.csv; .venv/bin/python catalog.py | grep inactive
   ```

Its change, against `task/`

```text
--- task/convert.py
+++ convert.py
@@ -12,8 +12,10 @@
 """
 
 import csv
+import os
 import sys
-from decimal import ROUND_HALF_UP, Decimal
+from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
+from pathlib import Path
 
 
 def to_cents(text):
@@ -29,19 +31,38 @@
 
 
 def convert(source, target):
+    """Convert ``source`` to ``target``.
+
+    The output is written to a temporary file next to ``target`` and renamed
+    only when the whole list was converted, so a failed conversion never
+    leaves a partial list behind for the job to load.
+    """
     rows = 0
-    with open(source, newline="", encoding="utf-8") as supplier, \
-            open(target, "w", newline="", encoding="utf-8") as out:
-        writer = csv.writer(out)
-        writer.writerow(("sku", "price_cents"))
-        for row in csv.DictReader(supplier, delimiter=";"):
-            if row["currency"].strip() != "EUR":
-                continue
-            cents = piece_cents(to_cents(row["price"]), row["pack"] or 1)
-            writer.writerow((row["article"].strip(), cents))
-            rows += 1
-            if rows % 10 == 0:
-                print(f"{rows} rows")
+    target = Path(target)
+    partial = target.with_name(target.name + ".partial")
+    try:
+        with open(source, newline="", encoding="utf-8") as supplier, \
+                open(partial, "w", newline="", encoding="utf-8") as out:
+            writer = csv.writer(out)
+            writer.writerow(("sku", "price_cents"))
+            reader = csv.DictReader(supplier, delimiter=";")
+            for row in reader:
+                if (row["currency"] or "").strip() != "EUR":
+                    continue
+                try:
+                    cents = piece_cents(to_cents(row["price"]), row["pack"] or 1)
+                except (InvalidOperation, ValueError, ZeroDivisionError, TypeError) as exc:
+                    raise ValueError(
+                        f"line {reader.line_num}: cannot read price {row['price']!r} "
+                        f"/ pack {row['pack']!r} of {row['article']!r}"
+                    ) from exc
+                writer.writerow((row["article"].strip(), cents))
+                rows += 1
+                if rows % 10 == 0:
+                    print(f"{rows} rows")
+        os.replace(partial, target)
+    finally:
+        partial.unlink(missing_ok=True)
     return rows
 
 
@@ -49,7 +70,11 @@
     if len(argv) != 3:
         print(__doc__, file=sys.stderr)
         return 2
-    rows = convert(argv[1], argv[2])
+    try:
+        rows = convert(argv[1], argv[2])
+    except ValueError as exc:
+        print(f"convert failed: {exc}", file=sys.stderr)
+        return 1
     print(f"done, {rows} rows")
     return 0
 
--- task/job.py
+++ job.py
@@ -38,8 +38,16 @@
     """Run the converter, a program of its own that purchasing also uses by hand."""
     command = [sys.executable, str(HERE / "convert.py"), str(supplier_list), str(staging)]
     log.info("running %s", " ".join(command))
-    # The converter reports its progress line by line; keep that out of cron's mail.
-    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
+    # The converter reports its progress line by line; keep that out of cron's mail,
+    # but keep its errors: a failed conversion must fail the job, not be loaded.
+    result = subprocess.run(
+        command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True
+    )
+    if result.returncode != 0:
+        detail = result.stderr.strip().splitlines()[-1:] or ["no message"]
+        raise ValueError(
+            f"converter exited with code {result.returncode}: {detail[0]}"
+        )
 
 
 def main(argv=None):
```

What the check said

```text
pass  a list with a price that is not a number: exit 2, 14 products not at the list's price
pass  a list of prices only: exit 0, not as expected: none
pass  a list without the price column: exit 2, catalog changed: no
fixed
```

## Every run

The first attempt of every run of every arm.

| Arm | Run | Check | Last line | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|
| `none` | 1 | passed | `fixed` | 9 | 130,217 | 59 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-none-1.jsonl) |
| `none` | 2 | passed | `fixed` | 9 | 111,863 | 54 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-none-2.jsonl) |
| `none` | 3 | passed | `fixed` | 7 | 115,072 | 66 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-none-3.jsonl) |
| `raw` | 1 | passed | `fixed` | 9 | 163,401 | 60 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-raw-1.jsonl) |
| `raw` | 2 | passed | `fixed` | 10 | 213,841 | 70 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-raw-2.jsonl) |
| `raw` | 3 | passed | `fixed` | 11 | 167,500 | 66 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-raw-3.jsonl) |
| `ormaos` | 1 | passed | `fixed` | 11 | 175,219 | 66 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-ormaos-1.jsonl) |
| `ormaos` | 2 | passed | `fixed` | 10 | 157,874 | 62 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-ormaos-2.jsonl) |
| `ormaos` | 3 | passed | `fixed` | 10 | 132,940 | 58 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/price-import-ormaos-3.jsonl) |

## The results files

- The benchmark: [fix](https://ormaos.com/benchmarks/fix/)
- Results folder: [`agent-bench/results/20261126-220703`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703): 2026-11-26, `claude-code / claude-opus-5-5`, bubblewrap, network open
