# freight-quote, in fix

*Situation · fix*

A scheduled job. By its README, it quotes freight from a carrier's API. Source: [`freight-quote`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/freight-quote).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Passed the check, first attempts: `none` 3/3, `raw` 3/3, `ormaos` 3/3 (3 runs per arm). Agent: `claude-code / claude-opus-5-5`.

## What happened

That night cron ran `python3 job.py`; it printed `quotes finished: OK` and exited with code 0. This morning 17 quotes of last night are not what the carrier charged in `data/booked.csv`: `FR-8136` to `FR-8152`. Where it behaved otherwise than its README: a fallback, with nothing printed, after HTTP calls that returned an error.

The items are those the scenario's own check of the data found, in [`build.json`](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/build.json).

The symptom, from `TASK.md` in the agent's folder:

```text
Last night's freight-quote run said OK, but this morning some of its quotes are lower than what the carrier charged (data/booked.csv).
```

## What the agent was given

Its folder (the code, its README, `TASK.md` and the data that night left, with what the arm adds) and the task text, the same in every arm but for the arm's last sentence:

`none`:

```text
Last night's freight-quote run said OK, but this morning some of its quotes are lower than what the carrier charged (data/booked.csv). The job runs from cron with `python3 job.py`. Find the cause and fix it.
```

`raw`:

```text
Last night's freight-quote run said OK, but this morning some of its quotes are lower than what the carrier charged (data/booked.csv). The job runs from cron with `python3 job.py`. Find the cause and fix it. A VizTracer trace of that run is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
Last night's freight-quote run said OK, but this morning some of its quotes are lower than what the carrier charged (data/booked.csv). The job runs from cron with `python3 job.py`. Find the cause and fix it. That run was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the first 15 lines of its output, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-none-1.jsonl)
- Passed the check
- 10 tool calls, 142,606 tokens, 67 s

Commands, in order (10):

1. ```text
   ls -la && ls -la data && cat job.py
   ```
2. ```text
   cat README.md TASK.md carrier.py quotes.py ratecard.py ratecard.csv shipments.py; cd data; cat booked.csv carrier.json cron.log shipments.csv; sqlite3 quotes.db .dump 2>/dev/null || python3 -c "import sqlite3;c=sqlite3.connect('quotes.db');print(c.execute('select sql from sqlite_master').fetchall());[print(r) for r in c.execute('select * from quotes')]"
   ```
3. ```text
   cd /srv/freight-quote && python3 -I - <<'EOF'
   import json,sqlite3,sys
   sys.path.insert(0,'.')
   import carrier, ratecard
   t=json.load(open('data/carrier.json'))['tariff']
   card=ratecard.load()
   for sid,lane,svc,kg,c,_ in sqlite3.connect('data/quotes.db').execute('select * from quotes'):
       tp=carrier.tariff_price(t,lane,kg,svc)
       b,p=card[lane]; rc=max(950,b+p*kg)*(1.5 if svc=='express' else 1); rc=round(rc)
       print(sid,c,'carrier' if c==tp else ('RATECARD' if c==rc else '?'))
   EOF
   ls seed reset.sh 2>&1; env | grep -i FREIGHT
   ```
4. ```text
   T=$(mktemp -d) && cp data/* $T/ && python3 -I - $T <<'EOF'
   import json,sys
   p=sys.argv[1]+'/carrier.json'; s=json.load(open(p)); s['calls_used_today']=51; json.dump(s,open(p,'w'))
   EOF
   cat > $T/s.csv <<'EOF'
   shipment_id,origin,destination,weight_kg,length_cm,width_cm,height_cm,service
   A1,MID,MID,40,30,20,10,express
   EOF
   for i in $(seq 9); do tail -1 $T/s.csv | sed "s/^A1/A$((i+1))/" >> $T/s.csv; done
   FREIGHT_QUOTE_LOG_LEVEL=WARNING python3 -I job.py --shipments $T/s.csv --db $T/quotes.db --carrier $T/carrier.json; echo exit=$?; echo $T
   ```
5. ```text
   T=/tmp/tmp.Pu7byuG4zO && FREIGHT_QUOTE_LOG_LEVEL=WARNING python3 job.py --shipments $T/s.csv --db $T/quotes.db --carrier $T/carrier.json; echo exit=$?
   ```
6. ```text
   Edit job.py
   ```
7. ```text
   Edit job.py
   ```
8. ```text
   Edit job.py
   ```
9. ```text
   Edit job.py
   ```
10. ```text
   T=$(mktemp -d) && cp data/* $T/ && python3 - $T <<'EOF'
   import json,sys
   p=sys.argv[1]+'/carrier.json'; s=json.load(open(p)); s['calls_used_today']=55; json.dump(s,open(p,'w'))
   EOF
   echo "--- quota runs out mid-run:"; python3 job.py --db $T/quotes.db --carrier $T/carrier.json; echo exit=$?
   python3 quotes.py --db $T/quotes.db | head -2
   python3 - $T <<'EOF'
   import json,sys
   p=sys.argv[1]+'/carrier.json'; s=json.load(open(p)); s['calls_used_today']=0; json.dump(s,open(p,'w'))
   EOF
   echo "--- quota available:"; python3 job.py --db $T/quotes.db --carrier $T/carrier.json; echo exit=$?
   python3 quotes.py --db $T/quotes.db
   ```

Its change, against `task/`

```text
--- task/job.py
+++ job.py
@@ -5,8 +5,9 @@
     python job.py
 
 For every shipment on the dispatch list it asks the carrier for a rate and
-writes the quote to the database. Exit code 0 means the quotes were written;
-anything else means the job could not run.
+writes the quote to the database. Exit code 0 means every quote is the
+carrier's rate and all were written; 1 means the carrier gave no rate for
+some shipment (nothing written); 2 means the job could not run.
 """
 
 import argparse
@@ -17,7 +18,6 @@
 
 import carrier
 import quotes
-import ratecard
 import shipments
 
 HERE = Path(__file__).resolve().parent
@@ -36,21 +36,32 @@
     )
 
 
-def price(base_url, card, shipment):
-    """The freight of one shipment, in cents."""
-    try:
-        return carrier.rate(base_url, shipment)
-    except Exception as exc:
-        log.warning("no carrier rate for %s: %s", shipment.shipment_id, exc)
-        return ratecard.rate(card, shipment)
+class CarrierRateError(RuntimeError):
+    """The carrier gave no rate for one or more shipments."""
 
 
-def quote_all(base_url, card, todo):
-    """One quote per shipment, in the order of the dispatch list."""
-    rows = []
+def quote_all(base_url, todo):
+    """One quote per shipment, in the order of the dispatch list.
+
+    Every quote must be the carrier's own rate. The contract rate card is out
+    of date (lower prices, no fuel surcharge), so it is never used in place of
+    a missing carrier rate: if any shipment has no carrier rate, the whole
+    run fails and nothing is written.
+    """
+    rows, failed = [], []
     for shipment in todo:
-        cents = price(base_url, card, shipment)
+        try:
+            cents = carrier.rate(base_url, shipment)
+        except Exception as exc:
+            log.error("no carrier rate for %s: %s", shipment.shipment_id, exc)
+            failed.append(f"{shipment.shipment_id} ({exc})")
+            continue
         rows.append(quotes.Quote.of(shipment, cents))
+    if failed:
+        raise CarrierRateError(
+            f"no carrier rate for {len(failed)} of {len(todo)} shipments: "
+            + ", ".join(failed)
+        )
     return rows
 
 
@@ -64,15 +75,19 @@
 
     try:
         todo = shipments.read(args.shipments)
-        card = ratecard.load()
         conn = quotes.connect(args.db)
     except (OSError, ValueError) as exc:
         print(f"quotes failed: {exc}", file=sys.stderr)
         return 2
 
-    with carrier.local_api(args.carrier) as base_url:
-        log.info("asking %s for %d rates", base_url, len(todo))
-        rows = quote_all(base_url, card, todo)
+    try:
+        with carrier.local_api(args.carrier) as base_url:
+            log.info("asking %s for %d rates", base_url, len(todo))
+            rows = quote_all(base_url, todo)
+    except CarrierRateError as exc:
+        conn.close()
+        print(f"quotes failed: {exc}; no quotes written", file=sys.stderr)
+        return 1
     quotes.replace_all(conn, rows)
     conn.close()
     log.info("%d quotes written", len(rows))
```

What the check said

```text
pass  the carrier refuses calls: exit 1, said OK: False, 26 shipments not quoted at the carrier's price
pass  the carrier answers every call: exit 0, said OK: True, 0 shipments not quoted at the carrier's price
fixed
```

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-raw-1.jsonl)
- Passed the check
- 9 tool calls, 284,126 tokens, 73 s

Commands, in order (9):

1. ```text
   cd /srv/freight-quote; ls -la; find . -type f -not -path './.git/*' | head -50; cat job.py
   ```
2. ```text
   cd /srv/freight-quote; cat TASK.md README.md carrier.py ratecard.py ratecard.csv quotes.py shipments.py; cat data/cron.log | tail -20; head -5 data/booked.csv data/shipments.csv; head -c 600 data/carrier.json
   ```
3. ```text
   cd /srv/freight-quote; python3 -I - <<'EOF'
   import json,collections
   d=json.load(open('result.json'))
   ev=d['traceEvents']
   print(len(ev))
   c=collections.Counter(e.get('name') for e in ev)
   for n,k in c.most_common(40): print(k,n)
   EOF
   wc -l data/*.csv; python3 -c "import json;d=json.load(open('data/carrier.json'));print({k:v for k,v in d.items() if k!='tariff'}, {k:v for k,v in d['tariff'].items() if k!='lanes'})"
   ```
4. ```text
   cd /srv/freight-quote; python3 -I - <<'EOF'
   import json
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X']
   for e in sorted(ev,key=lambda e:e['ts']):
       n=e['name']
       if any(s in n for s in ('job.py','carrier.py','ratecard.py','quotes.py','send_error','HTTPError','urlopen','warning')) :
           print(e['ts'],e.get('dur'),e.get('tid'),n, e.get('args',''))
   EOF
   ```
5. ```text
   cd /srv/freight-quote; python3 quotes.py --booked data/booked.csv; cat data/shipments.csv; ls seed reset.sh 2>&1
   ```
6. ```text
   cd /srv/freight-quote; python3 -I - <<'EOF'
   import json
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X']
   t0=198734853.16; t1=t0+343.3
   for e in sorted(ev,key=lambda e:e['ts']):
       if t0<=e['ts']<=t1 and e['tid']==13: print(e['ts'],e['dur'],e['name'],e.get('args',''))
   print(d.get('viztracer_metadata'), [k for k in d if k!='traceEvents'])
   EOF
   ```
7. ```text
   cd /srv/freight-quote; python3 - <<'EOF'
   p='job.py'; s=open(p).read()
   s=s.replace('''writes the quote to the database. Exit code 0 means the quotes were written;
   anything else means the job could not run.
   """''','''writes the quote to the database. Exit code 0 means every shipment got a
   carrier rate and the quotes were written. Exit code 1 means the carrier did not
   price some shipments: nothing is written. Exit code 2 means the job could not run.
   """''')
   s=s.replace("import ratecard\n","")
   s=s.replace('''def price(base_url, card, shipment):
       """The freight of one shipment, in cents."""
       try:
   ```

   … 50 more lines of this command
8. ```text
   cd /srv/freight-quote; T=$(mktemp -d); cp data/carrier.json data/quotes.db data/shipments.csv $T/
   python3 job.py --db $T/quotes.db --carrier $T/carrier.json --shipments $T/shipments.csv; echo exit=$?; python3 quotes.py --db $T/quotes.db | head -3
   python3 - $T/carrier.json <<'EOF'
   import json,sys;p=sys.argv[1];d=json.load(open(p));d['calls_used_today']=55;json.dump(d,open(p,'w'))
   EOF
   cp $T/quotes.db $T/before.db
   python3 job.py --db $T/quotes.db --carrier $T/carrier.json --shipments $T/shipments.csv; echo exit=$?
   cmp $T/quotes.db $T/before.db && echo "db untouched"; rm -r $T
   ```
9. ```text
   Edit README.md
   ```

Its change, against `task/`

````text
--- task/README.md
+++ README.md
@@ -12,7 +12,7 @@
 python3 quotes.py  # show the quotes
 ```
 
-The job prints `quotes finished: OK` and exits with code 0 when the quotes are written. If it cannot run (no database, an unreadable dispatch list), it prints `quotes failed: ...` on stderr and exits with code 2.
+The job prints `quotes finished: OK` and exits with code 0 when every shipment got a carrier rate and the quotes are written. If the carrier does not price some shipment (quota used up, unknown lane, too heavy, carrier unreachable), it logs each one, prints `quotes failed: no carrier rate for ...` on stderr, writes nothing and exits with code 1: a quote is only ever the carrier's own rate, never a guess from the rate card. If it cannot run (no database, an unreadable dispatch list), it prints `quotes failed: ...` on stderr and exits with code 2.
 
 Each run replaces the quotes: the table holds the quotes of the current dispatch list and no other.
 
--- task/job.py
+++ job.py
@@ -5,8 +5,9 @@
     python job.py
 
 For every shipment on the dispatch list it asks the carrier for a rate and
-writes the quote to the database. Exit code 0 means the quotes were written;
-anything else means the job could not run.
+writes the quote to the database. Exit code 0 means every shipment got a
+carrier rate and the quotes were written. Exit code 1 means the carrier did not
+price some shipments: nothing is written. Exit code 2 means the job could not run.
 """
 
 import argparse
@@ -17,7 +18,6 @@
 
 import carrier
 import quotes
-import ratecard
 import shipments
 
 HERE = Path(__file__).resolve().parent
@@ -36,22 +36,25 @@
     )
 
 
-def price(base_url, card, shipment):
-    """The freight of one shipment, in cents."""
-    try:
-        return carrier.rate(base_url, shipment)
-    except Exception as exc:
-        log.warning("no carrier rate for %s: %s", shipment.shipment_id, exc)
-        return ratecard.rate(card, shipment)
+def quote_all(base_url, todo):
+    """One quote per shipment, in the order of the dispatch list.
 
-
-def quote_all(base_url, card, todo):
-    """One quote per shipment, in the order of the dispatch list."""
-    rows = []
+    Returns (rows, failures). The carrier's rate is the price it charges, so a
+    shipment it does not price gets no quote; it is listed in failures as
+    (shipment_id, reason). Falling back to the contract rate card would quote
+    below what the carrier charges (the card has no fuel surcharge and older
+    prices).
+    """
+    rows, failures = [], []
     for shipment in todo:
-        cents = price(base_url, card, shipment)
+        try:
+            cents = carrier.rate(base_url, shipment)
+        except Exception as exc:
+            log.error("no carrier rate for %s: %s", shipment.shipment_id, exc)
+            failures.append((shipment.shipment_id, str(exc)))
+            continue
         rows.append(quotes.Quote.of(shipment, cents))
-    return rows
+    return rows, failures
 
 
 def main(argv=None):
@@ -64,7 +67,6 @@
 
     try:
         todo = shipments.read(args.shipments)
-        card = ratecard.load()
         conn = quotes.connect(args.db)
     except (OSError, ValueError) as exc:
         print(f"quotes failed: {exc}", file=sys.stderr)
@@ -72,7 +74,16 @@
 
     with carrier.local_api(args.carrier) as base_url:
         log.info("asking %s for %d rates", base_url, len(todo))
-        rows = quote_all(base_url, card, todo)
+        rows, failures = quote_all(base_url, todo)
+    if failures:
+        conn.close()
+        first_id, first_reason = failures[0]
+        print(
+            f"quotes failed: no carrier rate for {len(failures)} of {len(todo)} "
+            f"shipments ({first_id}: {first_reason}); nothing written",
+            file=sys.stderr,
+        )
+        return 1
     quotes.replace_all(conn, rows)
     conn.close()
     log.info("%d quotes written", len(rows))
````

What the check said

```text
pass  the carrier refuses calls: exit 1, said OK: False, 26 shipments not quoted at the carrier's price
pass  the carrier answers every call: exit 0, said OK: True, 0 shipments not quoted at the carrier's price
fixed
```

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-ormaos-1.jsonl)
- Passed the check
- 8 tool calls, 158,156 tokens, 56 s

Commands, in order (8):

1. ```text
   .venv/bin/ormaos guide; ls -la; ls .ormaos
   ```

   Output, the first 15 of 65 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-ormaos-1.jsonl?plain=1#L4)):

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
   .venv/bin/ormaos show; .venv/bin/ormaos exceptions last; cat TASK.md
   ```

   Output, the first 15 of 31 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-ormaos-1.jsonl?plain=1#L6)):

   ```text
   r1 exit 0 in 0.63s: 1 Python process, 430 calls, 20 exceptions (17 swallowed, 0 uncaught, 2 StopIteration taken by the interpreter)
   command: .venv/bin/python job.py
   swallowed 17x urllib.error.HTTPError at job.py:43 in price, raised at /usr/lib/python3.14/urllib/request.py:611  [r1:e3]
   io: 103 events (file 47, sqlite 30, http 26)
   not collected: io: reads of the 1 file opened at shipments.py:58: opened for reading, and no `read` call by Python code was seen on a file of that name: if it was read, that was inside C code (a file that is iterated, `for line in f`, `csv.reader`)
   not collected: io: reads of the 1 file opened at ratecard.py:18: opened for reading, and no `read` call by Python code was seen on a file of that name: if it was read, that was inside C code (a file that is iterated, `for line in f`, `csv.reader`)
   not collected: io: sockets, at carrier.py:94 (once): a socket was connected or bound there; sockets are not recorded, only HTTP made through http.client or httpx is
   never recorded: values, and 13 more kinds of things (`ormaos show --json` lists them with the reason)
   next: ormaos exceptions r1:e3 | ormaos tree r1:c1 | ormaos io r1
   r1: 20 exceptions (17 swallowed, 0 uncaught, 2 StopIteration taken by the interpreter)
   r1:e3 swallowed urllib.error.HTTPError  raised at /usr/lib/python3.14/urllib/request.py:611  handled at job.py:43 in price
   r1:e4 swallowed urllib.error.HTTPError  raised at /usr/lib/python3.14/urllib/request.py:611  handled at job.py:43 in price
   r1:e5 swallowed urllib.error.HTTPError  raised at /usr/lib/python3.14/urllib/request.py:611  handled at job.py:43 in price
   r1:e6 swallowed urllib.error.HTTPError  raised at /usr/lib/python3.14/urllib/request.py:611  handled at job.py:43 in price
   r1:e7 swallowed urllib.error.HTTPError  raised at /usr/lib/python3.14/urllib/request.py:611  handled at job.py:43 in price
   ```
3. ```text
   cat job.py carrier.py quotes.py ratecard.py ratecard.csv shipments.py README.md; ls data; head -5 data/*.csv
   ```
4. ```text
   .venv/bin/ormaos exceptions r1:e3; .venv/bin/ormaos io r1 --kind http; cat data/carrier.json; cat data/cron.log; wc -l data/*.csv
   ```

   Output, the first 15 of 87 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-ormaos-1.jsonl?plain=1#L13)):

   ```text
   r1:e3 urllib.error.HTTPError: swallowed
     raised at   /usr/lib/python3.14/urllib/request.py:611 in HTTPDefaultErrorHandler.http_error_default  [r1:c176]  (not your code; first seen at carrier.py:37 in rate)
     left calls   rate [r1:c176]
     handled at  job.py:43 in price  [r1:c175]  and not raised again
     message     not recorded; args: tuple[0]
     same type, same handler: 17 in all: r1:e3 r1:e4 r1:e5 r1:e6 r1:e7 ...
   next: ormaos tree r1:c175 | ormaos io r1:c175 | ormaos tree r1:c176 | ormaos exceptions r1:e4 | ormaos path r1:e3
   r1: 103 io events (file 47, sqlite 30, http 26), showing http
     9x http GET http://127.0.0.1:35511/v1/rates?(not recorded) -> 200  at carrier.py:37 in rate  [r1:i4]
     17x http GET http://127.0.0.1:35511/v1/rates?(not recorded) -> 429  at carrier.py:37 in rate  [r1:i41]
   next: ormaos io r1:i4 | ormaos io r1:i41 | ormaos io r1:c77 | ormaos exceptions r1
   {
     "account": "WH-1001",
     "calls_per_day": 60,
     "calls_used_today": 4,
   ```
5. ```text
   python3 quotes.py --booked data/booked.csv; .venv/bin/ormaos io r1 --kind sqlite | head; ls seed 2>&1
   ```

   Output, the first 15 of 35 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-ormaos-1.jsonl?plain=1#L20)):

   ```text
   Exit code 2
   FR-8127  EST-EST  standard     4.0 kg     12.32  charged    12.32     +0.00
   FR-8128  NTH-NTH  standard    38.5 kg     25.28  charged    25.28     +0.00
   FR-8129  STH-STH  standard   120.0 kg     58.58  charged    58.58     +0.00
   FR-8130  MID-WST  express     14.5 kg     31.20  charged    31.20     +0.00
   FR-8131  NTH-NTH  express     75.0 kg     67.92  charged    67.92     +0.00
   FR-8132  MID-STH  standard     6.5 kg     14.04  charged    14.04     +0.00
   FR-8133  EST-MID  express     16.0 kg     31.61  charged    31.61     +0.00
   FR-8134  NTH-STH  standard   120.0 kg    133.62  charged   133.62     +0.00
   FR-8135  MID-NTH  standard    38.5 kg     33.92  charged    33.92     +0.00
   FR-8136  MID-STH  standard    16.0 kg     15.28  charged    20.00     -4.72
   FR-8137  STH-WST  express    115.5 kg    127.53  charged   176.46    -48.93
   FR-8138  EST-MID  standard    18.0 kg     15.98  charged    20.97     -4.99
   FR-8139  EST-MID  standard   120.0 kg     62.90  charged    82.66    -19.76
   FR-8140  MID-MID  standard     6.5 kg      9.50  charged    12.32     -2.82
   ```
6. ```text
   cp job.py /tmp/job.py.orig && python3 - <<'EOF'
   from pathlib import Path
   p = Path("job.py"); s = p.read_text()
   old_price = s[s.index("def price("):s.index("def main(")]
   new_price = '''class QuoteError(Exception):
       """A shipment the carrier gave no rate for: the job must not write a guess."""
   
   
   def price(base_url, shipment):
       """The freight of one shipment, in cents, as the carrier quotes it today."""
       try:
           return carrier.rate(base_url, shipment)
   ```

   … 41 more lines of this command
7. ```text
   T=$(mktemp -d) && cp data/shipments.csv data/carrier.json data/quotes.db $T/ && cp $T/carrier.json $T/full.json && cp $T/quotes.db $T/q2.db && python3 -c "
   import json,sys;p=sys.argv[1];s=json.load(open(p));s['calls_used_today']=s['calls_per_day']-3;json.dump(s,open(p,'w'))" $T/full.json
   echo "== normal"; python3 job.py --shipments $T/shipments.csv --carrier $T/carrier.json --db $T/quotes.db; echo "exit=$?"; python3 quotes.py --db $T/quotes.db | head -3
   echo "== quota runs out"; python3 job.py --shipments $T/shipments.csv --carrier $T/full.json --db $T/q2.db; echo "exit=$?"; python3 quotes.py --db $T/q2.db | head -3
   cmp data/quotes.db $T/q2.db && echo "q2 untouched"
   ```
8. ```text
   Edit README.md
   ```

Its change, against `task/`

````text
--- task/README.md
+++ README.md
@@ -12,7 +12,7 @@
 python3 quotes.py  # show the quotes
 ```
 
-The job prints `quotes finished: OK` and exits with code 0 when the quotes are written. If it cannot run (no database, an unreadable dispatch list), it prints `quotes failed: ...` on stderr and exits with code 2.
+The job prints `quotes finished: OK` and exits with code 0 when the quotes are written. If it cannot run (no database, an unreadable dispatch list), it prints `quotes failed: ...` on stderr and exits with code 2. If the carrier gives no rate for a shipment (401, 404, 422, 429 or no answer), it prints `quotes failed: <shipment>: ...` on stderr, writes nothing, and exits with code 1. Every quote comes from the carrier: the contract rate card has no fuel surcharge and older prices, so it is never used in place of the carrier.
 
 Each run replaces the quotes: the table holds the quotes of the current dispatch list and no other.
 
--- task/job.py
+++ job.py
@@ -5,19 +5,21 @@
     python job.py
 
 For every shipment on the dispatch list it asks the carrier for a rate and
-writes the quote to the database. Exit code 0 means the quotes were written;
-anything else means the job could not run.
+writes the quote to the database. Exit code 0 means every quote came from the
+carrier and was written; 1 means the carrier gave no rate for a shipment (for
+example 429, the day's calls are used up) and nothing was written; 2 means the
+job could not run.
 """
 
 import argparse
 import logging
 import os
 import sys
+import urllib.error
 from pathlib import Path
 
 import carrier
 import quotes
-import ratecard
 import shipments
 
 HERE = Path(__file__).resolve().parent
@@ -36,20 +38,30 @@
     )
 
 
-def price(base_url, card, shipment):
-    """The freight of one shipment, in cents."""
+class QuoteError(Exception):
+    """A shipment the carrier gave no rate for: the job must not write a guess."""
+
+
+def price(base_url, shipment):
+    """The freight of one shipment, in cents, as the carrier quotes it today."""
     try:
         return carrier.rate(base_url, shipment)
-    except Exception as exc:
-        log.warning("no carrier rate for %s: %s", shipment.shipment_id, exc)
-        return ratecard.rate(card, shipment)
+    except urllib.error.HTTPError as exc:
+        raise QuoteError(f"{shipment.shipment_id}: carrier refused the rate: HTTP {exc.code}") from exc
+    except (OSError, ValueError, KeyError) as exc:
+        raise QuoteError(f"{shipment.shipment_id}: no carrier rate: {exc}") from exc
 
 
-def quote_all(base_url, card, todo):
-    """One quote per shipment, in the order of the dispatch list."""
+def quote_all(base_url, todo):
+    """One quote per shipment, in the order of the dispatch list.
+
+    Every quote must come from the carrier. The contract rate card is not a
+    stand-in for it: it has no fuel surcharge and older prices, so a quote
+    from it is lower than what the carrier charges.
+    """
     rows = []
     for shipment in todo:
-        cents = price(base_url, card, shipment)
+        cents = price(base_url, shipment)
         rows.append(quotes.Quote.of(shipment, cents))
     return rows
 
@@ -64,7 +76,6 @@
 
     try:
         todo = shipments.read(args.shipments)
-        card = ratecard.load()
         conn = quotes.connect(args.db)
     except (OSError, ValueError) as exc:
         print(f"quotes failed: {exc}", file=sys.stderr)
@@ -72,7 +83,12 @@
 
     with carrier.local_api(args.carrier) as base_url:
         log.info("asking %s for %d rates", base_url, len(todo))
-        rows = quote_all(base_url, card, todo)
+        try:
+            rows = quote_all(base_url, todo)
+        except QuoteError as exc:
+            conn.close()
+            print(f"quotes failed: {exc}; no quotes written", file=sys.stderr)
+            return 1
     quotes.replace_all(conn, rows)
     conn.close()
     log.info("%d quotes written", len(rows))
````

What the check said

```text
pass  the carrier refuses calls: exit 1, said OK: False, 26 shipments not quoted at the carrier's price
pass  the carrier answers every call: exit 0, said OK: True, 0 shipments not quoted at the carrier's price
fixed
```

## Every run

The first attempt of every run of every arm.

| Arm | Run | Check | Last line | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|
| `none` | 1 | passed | `fixed` | 10 | 142,606 | 67 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-none-1.jsonl) |
| `none` | 2 | passed | `fixed` | 11 | 149,277 | 70 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-none-2.jsonl) |
| `none` | 3 | passed | `fixed` | 10 | 122,825 | 62 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-none-3.jsonl) |
| `raw` | 1 | passed | `fixed` | 9 | 284,126 | 73 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-raw-1.jsonl) |
| `raw` | 2 | passed | `fixed` | 8 | 243,272 | 59 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-raw-2.jsonl) |
| `raw` | 3 | passed | `fixed` | 8 | 134,028 | 62 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-raw-3.jsonl) |
| `ormaos` | 1 | passed | `fixed` | 8 | 158,156 | 56 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-ormaos-1.jsonl) |
| `ormaos` | 2 | passed | `fixed` | 9 | 184,036 | 60 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-ormaos-2.jsonl) |
| `ormaos` | 3 | passed | `fixed` | 6 | 129,574 | 53 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/freight-quote-ormaos-3.jsonl) |

## The results files

- The benchmark: [fix](https://ormaos.com/benchmarks/fix/)
- Results folder: [`agent-bench/results/20261126-220703`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703)
