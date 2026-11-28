# order-sync, in fix

*Situation · fix*

A scheduled job. By its README, it applies orders to an inventory. Source: [`order-sync`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/order-sync).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Passed the check, first attempts:

- 2026-11-26, `claude-code / claude-opus-5-5`, bubblewrap, network open: `none` 3/3, `raw` 3/3, `ormaos` 3/3 (3 runs per arm)

## What happened

That night cron ran `python3 job.py --source api`; it printed `sync finished: OK` and exited with code 0. This morning the stock of 3 SKUs in `data/inventory.db` is not the warehouse's count in `data/count.csv`: `HDS-0402`, `KBD-0101` and `MON-0201`. Where it behaved otherwise than its README: an exception that is caught and not shown.

The items are those the scenario's own check of the data found, in [`build.json`](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/build.json).

The symptom, from `TASK.md` in the agent's folder:

```text
Last night's order sync run said OK, but this morning the stock of some products is not what the warehouse counted (data/count.csv).
```

## What the agent was given

Its folder (the code, its README, `TASK.md` and the data that night left, with what the arm adds) and the task text, the same in every arm but for the arm's last sentence:

`none`:

```text
Last night's order sync run said OK, but this morning the stock of some products is not what the warehouse counted (data/count.csv). The job runs from cron with `python3 job.py --source api`. Find the cause and fix it.
```

`raw`:

```text
Last night's order sync run said OK, but this morning the stock of some products is not what the warehouse counted (data/count.csv). The job runs from cron with `python3 job.py --source api`. Find the cause and fix it. A VizTracer trace of that run is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
Last night's order sync run said OK, but this morning the stock of some products is not what the warehouse counted (data/count.csv). The job runs from cron with `python3 job.py --source api`. Find the cause and fix it. That run was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the first 15 lines of its output, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-none-1.jsonl)
- Passed the check
- 10 tool calls, 208,668 tokens, 93 s

Commands, in order (10):

1. ```text
   ls -laR | head -50 && cat job.py
   ```
2. ```text
   cat TASK.md README.md fetch.py inventory.py parse.py validate.py; for f in data/*.csv data/cron.log; do echo "== $f"; cat $f; done
   ```
3. ```text
   python3 -I inventory.py --count data/count.csv; sqlite3 data/inventory.db "select * from stock; select * from applied_orders; select * from backorders;" 2>/dev/null || python3 -I -c "
   import sqlite3;c=sqlite3.connect('file:data/inventory.db?mode=ro',uri=True)
   for t in ('stock','applied_orders','backorders'):
     print('==',t)
     for r in c.execute(f'select * from {t}'): print(r)"
   ```
4. ```text
   ls -la .. ; find / -path /proc -prune -o \( -name 'seed' -o -name '.ormaos' -o -name 'reset.sh' -o -name '*order*.csv' \) -print 2>/dev/null | grep -v ^/proc | head; crontab -l 2>/dev/null; ls /opt
   ```
5. ```text
   cd /tmp && rm -rf os-test && mkdir os-test && cp /srv/order-sync/data/inventory.db os-test/ && cd /srv/order-sync && ORDER_SYNC_LOG_LEVEL=INFO python3 -I job.py --source api --db /tmp/os-test/inventory.db; echo exit=$?
   ```
6. ```text
   ORDER_SYNC_LOG_LEVEL=INFO python3 job.py --source api --db /tmp/os-test/inventory.db; echo exit=$?; python3 inventory.py --db /tmp/os-test/inventory.db --count data/count.csv
   ```
7. ```text
   cp -a . /tmp/order-sync.bak && python3 - <<'EOF'
   import re
   p='inventory.py'; s=open(p).read()
   s=s.replace('''    quantity  INTEGER NOT NULL
   );
   """
   ''','''    quantity  INTEGER NOT NULL
   );
   """
   
   # Orders that could not be applied. The sales API hands an order over only
   # once, so the raw row is kept here to be fixed and applied by hand.
   ```

   … 45 more lines of this command
8. ```text
   python3 - <<'EOF'
   p='job.py'; s=open(p).read()
   old_start=s.index('def load_orders'); old_end=s.index('def main')
   s=s[:old_start]+'''def load_rows(source, orders_csv):
       """Fetch the raw rows from the chosen source."""
       if source == "api":
           with fetch.local_api(orders_csv) as base_url:
               log.info("fetching orders from %s", base_url)
               return fetch.from_api(base_url)
       log.info("reading orders from %s", orders_csv)
       return fetch.from_csv(orders_csv)
   
   ```

   … 74 more lines of this command
9. ```text
   cp data/inventory.db /tmp/os-test/inventory.db && cat > /tmp/os-test/bad.csv <<'EOF'
   order_id,placed_at,sku,quantity,channel,unit
   SO-90001,2026-11-26T06:10,kbd-0101,3,marketplace,each
   SO-90002,2026-11-26T06:11,HDS-0402,900,web,each
   SO-90003,2026-11-26T06:12,MON-0201,1,web,box
   SO-90004,2026-11-26T06:13,XYZ-9999,1,web,each
   SO-90005,2026-11-26T06:14,KBD-0101 ,2,web,each
   SO-90006,not-a-date,KBD-0101,1,web,each
   SO-90007,2026-11-26T06:15,MSE-0102,1,web,each
   EOF
   python3 job.py --source api --orders /tmp/os-test/bad.csv --db /tmp/os-test/inventory.db; echo exit=$?
   python3 -c "
   ```

   … 4 more lines of this command
10. ```text
   python3 - <<'EOF'
   p='README.md'; s=open(p).read()
   old="The job prints `sync finished: OK` and exits with code 0 when the sync is done."
   assert old in s
   s=s.replace(old,"The job prints `sync finished: OK` and exits with code 0 when every order was applied. If some orders are rejected (bad SKU, quantity, unit or date, or a SKU not in the inventory), each one is logged at ERROR, kept with its raw data and the reason in the `rejected_orders` table, and the job exits with code 1. The other orders are still applied.")
   open(p,'w').write(s)
   EOF
   ```

Its change, against `task/`

````text
--- task/README.md
+++ README.md
@@ -12,7 +12,7 @@
 python3 inventory.py  # show the stock levels
 ```
 
-The job prints `sync finished: OK` and exits with code 0 when the sync is done. If it cannot run (no database, unreadable export), it prints `sync failed: ...` on stderr and exits with code 2.
+The job prints `sync finished: OK` and exits with code 0 when every order was applied. If some orders are rejected (bad SKU, quantity, unit or date, or a SKU not in the inventory), each one is logged at ERROR, kept with its raw data and the reason in the `rejected_orders` table, and the job exits with code 1. The other orders are still applied. If it cannot run (no database, unreadable export), it prints `sync failed: ...` on stderr and exits with code 2.
 
 Running the job again over the same orders is safe: an order is applied only once.
 
--- task/inventory.py
+++ inventory.py
@@ -36,6 +36,18 @@
 );
 """
 
+# Orders that could not be applied. The sales API hands an order over only
+# once, so the raw row is kept here to be fixed and applied by hand.
+REJECTED_SCHEMA = """
+CREATE TABLE IF NOT EXISTS rejected_orders (
+    id           INTEGER PRIMARY KEY AUTOINCREMENT,
+    order_id     TEXT,
+    raw          TEXT NOT NULL,
+    reason       TEXT NOT NULL,
+    rejected_at  TEXT NOT NULL
+);
+"""
+
 
 class UnknownSkuError(LookupError):
     """The order names a SKU that the warehouse does not stock."""
@@ -44,7 +56,25 @@
 def connect(db_path=DEFAULT_DB):
     if not Path(db_path).exists():
         raise FileNotFoundError(f"{db_path} does not exist; run ./reset.sh first")
-    return sqlite3.connect(db_path)
+    conn = sqlite3.connect(db_path)
+    with conn:
+        conn.executescript(REJECTED_SCHEMA)
+    return conn
+
+
+def record_rejected(conn, order_id, raw, reason):
+    """Keep an order that could not be applied, with the reason."""
+    with conn:
+        conn.execute(
+            "INSERT INTO rejected_orders (order_id, raw, reason, rejected_at) "
+            "VALUES (?, ?, ?, ?)",
+            (
+                order_id,
+                raw,
+                reason,
+                datetime.now(timezone.utc).isoformat(timespec="seconds"),
+            ),
+        )
 
 
 def create(db_path, stock_csv):
@@ -61,6 +91,7 @@
     conn = sqlite3.connect(db_path)
     with conn:
         conn.executescript(SCHEMA)
+        conn.executescript(REJECTED_SCHEMA)
         conn.executemany(
             "INSERT INTO stock (sku, name, on_hand, pack_size) VALUES (?, ?, ?, ?)", rows
         )
--- task/job.py
+++ job.py
@@ -5,10 +5,13 @@
     python job.py                 # read the CSV export
     python job.py --source api    # ask the sales API instead
 
-Exit code 0 means the sync finished; anything else means it could not run.
+Exit code 0 means every order was applied. Exit code 1 means some orders were
+rejected (kept in the rejected_orders table, not applied). Exit code 2 means
+the job could not run.
 """
 
 import argparse
+import json
 import logging
 import os
 import sys
@@ -34,30 +37,58 @@
     )
 
 
-def load_orders(source, orders_csv):
-    """Fetch the raw rows from the chosen source and parse them."""
+def load_rows(source, orders_csv):
+    """Fetch the raw rows from the chosen source."""
     if source == "api":
         with fetch.local_api(orders_csv) as base_url:
             log.info("fetching orders from %s", base_url)
-            rows = fetch.from_api(base_url)
-    else:
-        log.info("reading orders from %s", orders_csv)
-        rows = fetch.from_csv(orders_csv)
-    return parse.parse_rows(rows)
+            return fetch.from_api(base_url)
+    log.info("reading orders from %s", orders_csv)
+    return fetch.from_csv(orders_csv)
 
 
-def sync_orders(conn, orders):
-    """Apply every order to the inventory. Returns how many were applied now."""
+def reject(conn, row, exc):
+    """Keep a row that could not be applied and say so loudly.
+
+    The sales API hands an order over only once: a row dropped here would be
+    lost for good, so it goes to the rejected_orders table instead.
+    """
+    order_id = row.get("order_id") if isinstance(row, dict) else None
+    reason = f"{type(exc).__name__}: {exc}"
+    log.error("order %s rejected: %s", order_id, reason)
+    inventory.record_rejected(
+        conn, order_id, json.dumps(row, default=str, sort_keys=True), reason
+    )
+
+
+def sync_orders(conn, rows):
+    """Parse, check and apply every row.
+
+    Returns (applied, rejected): how many orders were applied now and how
+    many were rejected (and kept in rejected_orders).
+    """
+    parsed = []
+    rejected = 0
+    for row in rows:
+        try:
+            order = parse.parse_row(row)
+            validate.check_order(order)
+        except (parse.ParseError, validate.ValidationError) as exc:
+            reject(conn, row, exc)
+            rejected += 1
+            continue
+        parsed.append((order, row))
+    parsed.sort(key=lambda item: (item[0].placed_at, item[0].order_id))
+
     applied = 0
-    for order in orders:
+    for order, row in parsed:
         try:
-            validate.check_order(order)
             if inventory.apply_order(conn, order):
                 applied += 1
-        except Exception as exc:
-            log.warning("order %s skipped: %s", order.order_id, exc)
-            continue
-    return applied
+        except inventory.UnknownSkuError as exc:
+            reject(conn, row, exc)
+            rejected += 1
+    return applied, rejected
 
 
 def main(argv=None):
@@ -70,14 +101,24 @@
 
     try:
         conn = inventory.connect(args.db)
-        orders = load_orders(args.source, args.orders)
-    except (OSError, parse.ParseError) as exc:
+        rows = load_rows(args.source, args.orders)
+    except OSError as exc:
         print(f"sync failed: {exc}", file=sys.stderr)
         return 2
 
-    applied = sync_orders(conn, orders)
+    applied, rejected = sync_orders(conn, rows)
     conn.close()
-    log.info("%d orders read, %d applied in this run", len(orders), applied)
+    log.info(
+        "%d orders read, %d applied in this run, %d rejected",
+        len(rows), applied, rejected,
+    )
+    if rejected:
+        print(
+            f"sync finished: {rejected} order(s) REJECTED and not applied; "
+            "see the rejected_orders table",
+            file=sys.stderr,
+        )
+        return 1
     print("sync finished: OK")
     return 0
 
--- task/parse.py
+++ parse.py
@@ -35,7 +35,7 @@
     return Order(
         order_id=row["order_id"].strip(),
         placed_at=placed_at,
-        sku=row["sku"],
+        sku=row["sku"].strip(),
         quantity=quantity,
         channel=row["channel"].strip(),
         unit=(row.get("unit") or DEFAULT_UNIT).strip().lower(),
````

What the check said

```text
pass  orders with a SKU in a bad format: exit 1, said OK: False, stock that is not the count: ['HDS-0402', 'KBD-0101']
pass  the same orders, well formed: exit 0, said OK: True, stock that is not the count: none
fixed
```

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-raw-1.jsonl)
- Passed the check
- 13 tool calls, 376,322 tokens, 88 s

Commands, in order (13):

1. ```text
   cd /srv/order-sync; ls -la; find . -type f | grep -v '^./.git/' | head -50; wc -c result.json
   ```
2. ```text
   cd /srv/order-sync; cat TASK.md README.md job.py fetch.py inventory.py parse.py validate.py; cat data/cron.log | tail -30; head -5 data/*.csv; wc -l data/*.csv
   ```
3. ```text
   cd /srv/order-sync; cat data/orders.csv; python3 inventory.py --count data/count.csv; python3 -I - <<'EOF'
   import json,collections
   d=json.load(open('result.json'))
   ev=d['traceEvents']
   print(len(ev), d.keys())
   c=collections.Counter(e.get('name') for e in ev)
   for n,k in c.most_common():
       if any(s in n for s in ('job.py','fetch','parse','validate','inventory','Error','check','apply')): print(k,n)
   print([e for e in ev if e.get('ph')!='X'][:10])
   EOF
   ```
4. ```text
   cd /srv/order-sync; python3 -I - <<'EOF'
   import json
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X']
   print(d['viztracer_metadata'])
   s=[e for e in ev if e['name'].startswith('sync_orders')][0]
   t0,t1=s['ts'],s['ts']+s['dur']
   for e in sorted(ev,key=lambda e:e['ts']):
       if t0<=e['ts']<=t1 and ('order-sync' in e['name'] or 'sqlite' in e['name'] or 'warning' in e['name'].lower() or 'Error' in e['name']):
           print(e['ts']-t0, e['dur'], e['name'], e.get('args',''))
   EOF
   ```
5. ```text
   cd /srv/order-sync; python3 -I - <<'EOF'
   import sqlite3
   c=sqlite3.connect('file:data/inventory.db?mode=ro',uri=True)
   for t in ('stock','applied_orders','backorders'):
       print(t); [print(r) for r in c.execute(f'select * from {t}')]
   EOF
   cat data/cron.log; python3 -I -c "
   import json;d=json.load(open('result.json'));print(list(d['file_info'].keys()) if isinstance(d['file_info'],dict) else d['file_info'])"
   ```
6. ```text
   cd /srv/order-sync; python3 -I - <<'EOF'
   import json
   d=json.load(open('result.json'))
   fi=d['file_info']
   print(list(fi['files'].keys()))
   for k,v in fi['files'].items():
       if 'order-sync' in k: print(k, type(v), (v[0][:3000] if isinstance(v,list) else str(v)[:300]) if 'validate' in k or 'parse' in k else '')
   EOF
   ```
7. ```text
   cd /srv/order-sync; mkdir -p /tmp/os-backup && cp -a job.py parse.py inventory.py data/inventory.db /tmp/os-backup/; ls seed reset.sh 2>&1
   ```
8. ```text
   Edit parse.py
   ```
9. ```text
   Edit inventory.py
   ```
10. ```text
   Edit inventory.py
   ```
11. ```text
   Edit inventory.py
   ```
12. ```text
   cd /srv/order-sync; python3 - <<'EOF'
   p='job.py'; s=open(p).read()
   old=s[s.index('def sync_orders'):s.index('def main')]
   new='''def sync_orders(conn, orders):
       """Apply every order to the inventory.
   
       Returns (applied, rejected): how many orders were applied now, and a list
       of (order, reason) for the orders that could not be applied. Rejected
       orders are stored in the ``rejected_orders`` table: the sales API will not
       hand them over again, so they must not just be dropped.
       """
       applied = 0
   ```

   … 49 more lines of this command
13. ```text
   mkdir -p /tmp/os-test && cd /tmp/os-test && cp /tmp/os-backup/inventory.db t.db && cat > o.csv <<'EOF'
   order_id,placed_at,sku,quantity,channel,unit
   SO-90001,2026-11-26T06:10,kbd-0101 ,2,web,each
   SO-90002,2026-11-26T06:11,MON-0201,0,web,each
   SO-90003,2026-11-26T06:12,XYZ-9999,1,web,each
   SO-90004,2026-11-26T06:13,HDS-0402,1,web,each
   EOF
   cd /srv/order-sync; python3 job.py --source api --orders /tmp/os-test/o.csv --db /tmp/os-test/t.db; echo exit=$?
   python3 -c "
   import sqlite3;c=sqlite3.connect('/tmp/os-test/t.db')
   print(c.execute('select * from rejected_orders').fetchall()); print(c.execute(\"select * from stock where sku in ('KBD-0101','HDS-0402')\").fetchall())"
   python3 job.py --orders data/orders.csv --db /tmp/os-test/t.db; echo exit=$?
   ```

Its change, against `task/`

```text
--- task/inventory.py
+++ inventory.py
@@ -36,6 +36,21 @@
 );
 """
 
+# Orders the job could not apply. The sales API hands an order over only once,
+# so a rejected order must be kept here or it is lost for good.
+REJECTED_SCHEMA = """
+CREATE TABLE IF NOT EXISTS rejected_orders (
+    order_id     TEXT PRIMARY KEY,
+    placed_at    TEXT NOT NULL,
+    sku          TEXT NOT NULL,
+    quantity     INTEGER NOT NULL,
+    channel      TEXT NOT NULL,
+    unit         TEXT NOT NULL,
+    reason       TEXT NOT NULL,
+    rejected_at  TEXT NOT NULL
+);
+"""
+
 
 class UnknownSkuError(LookupError):
     """The order names a SKU that the warehouse does not stock."""
@@ -44,7 +59,36 @@
 def connect(db_path=DEFAULT_DB):
     if not Path(db_path).exists():
         raise FileNotFoundError(f"{db_path} does not exist; run ./reset.sh first")
-    return sqlite3.connect(db_path)
+    conn = sqlite3.connect(db_path)
+    with conn:
+        conn.executescript(REJECTED_SCHEMA)
+    return conn
+
+
+def record_rejected(conn, order, reason):
+    """Keep an order that could not be applied, so it can be fixed and replayed."""
+    with conn:
+        conn.execute(
+            "INSERT OR REPLACE INTO rejected_orders "
+            "(order_id, placed_at, sku, quantity, channel, unit, reason, rejected_at) "
+            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
+            (
+                order.order_id,
+                order.placed_at.isoformat(),
+                order.sku,
+                order.quantity,
+                order.channel,
+                order.unit,
+                reason,
+                datetime.now(timezone.utc).isoformat(timespec="seconds"),
+            ),
+        )
+
+
+def clear_rejected(conn, order_id):
+    """Forget an earlier rejection once the order has been applied."""
+    with conn:
+        conn.execute("DELETE FROM rejected_orders WHERE order_id = ?", (order_id,))
 
 
 def create(db_path, stock_csv):
--- task/job.py
+++ job.py
@@ -5,7 +5,8 @@
     python job.py                 # read the CSV export
     python job.py --source api    # ask the sales API instead
 
-Exit code 0 means the sync finished; anything else means it could not run.
+Exit code 0 means every order was applied; 1 means the sync ran but some
+orders were rejected (see table rejected_orders); 2 means it could not run.
 """
 
 import argparse
@@ -47,17 +48,26 @@
 
 
 def sync_orders(conn, orders):
-    """Apply every order to the inventory. Returns how many were applied now."""
+    """Apply every order to the inventory.
+
+    Returns (applied, rejected): how many orders were applied now, and a list
+    of (order, reason) for the orders that could not be applied. Rejected
+    orders are stored in the ``rejected_orders`` table: the sales API will not
+    hand them over again, so they must not just be dropped.
+    """
     applied = 0
+    rejected = []
     for order in orders:
         try:
             validate.check_order(order)
             if inventory.apply_order(conn, order):
                 applied += 1
-        except Exception as exc:
-            log.warning("order %s skipped: %s", order.order_id, exc)
-            continue
-    return applied
+            inventory.clear_rejected(conn, order.order_id)
+        except (validate.ValidationError, inventory.UnknownSkuError) as exc:
+            log.error("order %s rejected: %s", order.order_id, exc)
+            inventory.record_rejected(conn, order, str(exc))
+            rejected.append((order, str(exc)))
+    return applied, rejected
 
 
 def main(argv=None):
@@ -75,9 +85,24 @@
         print(f"sync failed: {exc}", file=sys.stderr)
         return 2
 
-    applied = sync_orders(conn, orders)
+    applied, rejected = sync_orders(conn, orders)
     conn.close()
     log.info("%d orders read, %d applied in this run", len(orders), applied)
+    if rejected:
+        # Printed in full: cron mails it, and it is all that is kept of a run.
+        print(
+            f"sync finished with errors: {len(rejected)} of {len(orders)} orders "
+            f"rejected (kept in table rejected_orders)",
+            file=sys.stderr,
+        )
+        for order, reason in rejected:
+            print(
+                f"  rejected {order.order_id} placed_at={order.placed_at.isoformat()} "
+                f"sku={order.sku!r} quantity={order.quantity} unit={order.unit} "
+                f"channel={order.channel}: {reason}",
+                file=sys.stderr,
+            )
+        return 1
     print("sync finished: OK")
     return 0
 
--- task/parse.py
+++ parse.py
@@ -35,7 +35,9 @@
     return Order(
         order_id=row["order_id"].strip(),
         placed_at=placed_at,
-        sku=row["sku"],
+        # Exports and the API are not consistent about case and padding
+        # ("kbd-0101", "KBD-0101 "); the warehouse SKU is upper case.
+        sku=row["sku"].strip().upper(),
         quantity=quantity,
         channel=row["channel"].strip(),
         unit=(row.get("unit") or DEFAULT_UNIT).strip().lower(),
```

What the check said

```text
pass  orders with a SKU in a bad format: exit 0, said OK: True, stock that is not the count: none
pass  the same orders, well formed: exit 0, said OK: True, stock that is not the count: none
fixed
```

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-ormaos-1.jsonl)
- Passed the check
- 14 tool calls, 300,076 tokens, 94 s

Commands, in order (14):

1. ```text
   .venv/bin/ormaos guide; ls -la; ls -la .ormaos data
   ```

   Output, the first 15 of 78 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-ormaos-1.jsonl?plain=1#L5)):

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
   .venv/bin/ormaos show; cat TASK.md README.md data/count.csv data/cron.log data/orders.csv
   ```

   Output, the first 15 of 127 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-ormaos-1.jsonl?plain=1#L7)):

   ```text
   r1 exit 0 in 0.60s: 1 Python process, 240 calls, 6 exceptions (5 swallowed, 0 uncaught)
   command: .venv/bin/python job.py --source <str[3]>
   swallowed 5x validate.SkuFormatError at job.py:57 in sync_orders, raised at validate.py:24  [r1:e1]
   io: 123 events (sqlite 121, http 1, file 1)
   not collected: io: reads of the 1 file opened at fetch.py:26: opened for reading, and no `read` call by Python code was seen on a file of that name: if it was read, that was inside C code (a file that is iterated, `for line in f`, `csv.reader`)
   not collected: io: sockets, at fetch.py:60 (once): a socket was connected or bound there; sockets are not recorded, only HTTP made through http.client or httpx is
   never recorded: values, and 13 more kinds of things (`ormaos show --json` lists them with the reason)
   next: ormaos exceptions r1:e1 | ormaos tree r1:c1 | ormaos io r1
   Last night's order sync run said OK, but this morning the stock of some products is not what the warehouse counted (data/count.csv).
   # order-sync
   
   A scheduled job that takes the new orders from the sales system and applies them to the warehouse inventory: for every order, the ordered quantity leaves the stock of that SKU.
   
   It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.
   
   ```
3. ```text
   cat job.py fetch.py parse.py validate.py inventory.py
   ```
4. ```text
   .venv/bin/ormaos exceptions r1; .venv/bin/ormaos exceptions r1:e1; .venv/bin/python inventory.py --count data/count.csv; sqlite3 data/inventory.db "select * from applied_orders; select * from backorders; select * from stock" 2>&1 || .venv/bin/python -c "
   import sqlite3;c=sqlite3.connect('data/inventory.db')
   for t in ('applied_orders','backorders','stock'): print(t, c.execute(f'select * from {t}').fetchall())"
   ```

   Output, the first 15 of 28 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-ormaos-1.jsonl?plain=1#L14)):

   ```text
   r1: 6 exceptions (5 swallowed, 0 uncaught)
   r1:e1 swallowed validate.SkuFormatError  raised at validate.py:24  handled at job.py:57 in sync_orders
   r1:e2 swallowed validate.SkuFormatError  raised at validate.py:24  handled at job.py:57 in sync_orders
   r1:e3 swallowed validate.SkuFormatError  raised at validate.py:24  handled at job.py:57 in sync_orders
   r1:e4 swallowed validate.SkuFormatError  raised at validate.py:24  handled at job.py:57 in sync_orders
   r1:e5 swallowed validate.SkuFormatError  raised at validate.py:24  handled at job.py:57 in sync_orders
   r1:e6 exit SystemExit  raised at job.py:86
   next: ormaos exceptions r1:e1 | ormaos exceptions r1:e2 | ormaos tree r1:c106
   r1:e1 validate.SkuFormatError: swallowed
     raised at   validate.py:24 in check_sku  [r1:c154]
     left calls   check_sku [r1:c154], check_order [r1:c153]
     handled at  job.py:57 in sync_orders  [r1:c106]  and not raised again
     message     not recorded; args: tuple[1 str]
     same type, same handler: 5 in all: r1:e1 r1:e2 r1:e3 r1:e4 r1:e5
   next: ormaos tree r1:c106 | ormaos io r1:c106 | ormaos tree r1:c154 | ormaos exceptions r1:e2 | ormaos path r1:e1
   ```
5. ```text
   .venv/bin/ormaos tree r1:c1 --depth 3 --limit 60; .venv/bin/ormaos tree r1:c153; .venv/bin/ormaos io r1
   ```

   Output, the first 15 of 78 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-ormaos-1.jsonl?plain=1#L20)):

   ```text
   r1:c1 <module>() -> raised  job.py:1  567.7ms  io 122  calls below: 5
     r1:c2 <module>() -> NoneType  fetch.py:1  23.5ms
     r1:c3 <module>() -> NoneType  inventory.py:1  1.1ms  calls below: 1
       r1:c4 UnknownSkuError() -> NoneType  inventory.py:40  8us
     r1:c5 <module>() -> NoneType  parse.py:1  740us  calls below: 5
       r1:c6 ParseError() -> NoneType  parse.py:11  5us
       r1:c7 Order() -> NoneType  parse.py:15  6us
       r1:c8 Order.__annotate__(format: int) -> dict[6]  parse.py:15  10us
       r1:c9 <module>() -> NoneType  <string>:1  8us
       r1:c10 __create_fn__(__dataclass_HAS_DEFAULT_FACTORY__: dataclasses._HAS_DEFAULT_FACTORY_CLASS, __dataclass_...) -> tuple[6 function]  <string>:1  21us
     r1:c11 <module>() -> NoneType  validate.py:1  156us  calls below: 4
       r1:c12 ValidationError() -> NoneType  validate.py:10  6us
       r1:c13 SkuFormatError() -> NoneType  validate.py:14  5us
       r1:c14 QuantityError() -> NoneType  validate.py:18  4us
       r1:c15 UnitError() -> NoneType  validate.py:38  4us
   ```
6. ```text
   for e in 2 3 4 5; do .venv/bin/ormaos exceptions r1:e$e | head -2; done; .venv/bin/ormaos tree r1:c106 --offset 37; .venv/bin/ormaos tree r1:c27 --limit 10; .venv/bin/ormaos show --json | .venv/bin/python -m json.tool | head -80
   ```

   Output, the first 15 of 133 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-ormaos-1.jsonl?plain=1#L25)):

   ```text
   r1:e2 validate.SkuFormatError: swallowed
     raised at   validate.py:24 in check_sku  [r1:c180]
   r1:e3 validate.SkuFormatError: swallowed
     raised at   validate.py:24 in check_sku  [r1:c200]
   r1:e4 validate.SkuFormatError: swallowed
     raised at   validate.py:24 in check_sku  [r1:c214]
   r1:e5 validate.SkuFormatError: swallowed
     raised at   validate.py:24 in check_sku  [r1:c234]
   inside: r1:c1 <module> > r1:c16 main
   r1:c106 sync_orders(conn: sqlite3.Connection, orders: list[26 parse.Order]) -> int  job.py:49  9.8ms  io 120  [swallowed 5x validate.SkuFormatError: r1:e1]  calls below: 47
     r1:c213 check_order(order: parse.Order) -> raised  validate.py:47  45us  calls below: 1
       r1:c214 check_sku(sku: str[8]) -> raised  validate.py:22  27us
     r1:c215 check_order(order: parse.Order) -> NoneType  validate.py:47  49us  calls below: 3
       r1:c216 check_sku(sku: str[8]) -> NoneType  validate.py:22  6us
       r1:c217 check_quantity(quantity: int) -> NoneType  validate.py:27  5us
   ```
7. ```text
   .venv/bin/python -c "
   import sqlite3;c=sqlite3.connect('data/inventory.db')
   ids={r[0] for r in c.execute('select order_id from applied_orders')}
   print([f'SO-{n}' for n in range(20501,20539) if f'SO-{n}' not in ids])"; ls seed reset.sh 2>&1
   ```
8. ```text
   Edit parse.py
   ```
9. ```text
   Edit parse.py
   ```
10. ```text
   Edit parse.py
   ```
11. ```text
   .venv/bin/python - <<'EOF'
   from pathlib import Path
   p=Path("job.py"); s=p.read_text()
   s=s.replace('''import argparse
   import logging''','''import argparse
   import csv
   import logging''')
   s=s.replace('''DEFAULT_ORDERS = HERE / "data" / "orders.csv"
   ''','''DEFAULT_ORDERS = HERE / "data" / "orders.csv"
   # Orders that could not be applied. The sales API hands an order over only
   # once, so a rejected order is kept here (in the export's format) to be fixed
   # and replayed with: python3 job.py --orders data/rejected_orders.csv
   ```

   … 86 more lines of this command
12. ```text
   T=$(mktemp -d) && cp data/inventory.db $T/ && .venv/bin/python -c "
   import sqlite3;c=sqlite3.connect('$T/inventory.db');c.execute(\"delete from applied_orders where order_id>='SO-20538'\");c.execute(\"update stock set on_hand=on_hand+4 where sku='CAB-0302'\");c.commit()" && cat > $T/orders.csv <<'EOF'
   order_id,placed_at,sku,quantity,channel,unit
   SO-90001,2026-11-26T01:00,kbd-0101,2,marketplace,each
   SO-90002,2026-11-26T01:01, HDS-0402 ,1,web,each
   SO-90003,2026-11-26T01:02,MON–0201,1,web,each
   SO-90004,2026-11-26T01:03,ＫＢＤ-0101,1,web,each
   SO-90005,2026-11-26T01:04,XYZ-9999,1,web,each
   SO-90006,2026-11-26T01:05,KBD-01O1,1,web,each
   EOF
   cat data/orders.csv | tail -n +2 >> $T/orders.csv
   .venv/bin/python -I job.py --source api --orders $T/orders.csv --db $T/inventory.db --rejected $T/rej.csv; echo "exit=$?"; cat $T/rej.csv
   ```

   … 3 more lines of this command
13. ```text
   T=$(mktemp -d) && cp data/inventory.db $T/ && .venv/bin/python -c "
   import sqlite3;c=sqlite3.connect('$T/inventory.db');c.execute(\"delete from applied_orders where order_id>='SO-20538'\");c.execute(\"update stock set on_hand=on_hand+4 where sku='CAB-0302'\");c.commit()" && cat > $T/orders.csv <<'EOF'
   order_id,placed_at,sku,quantity,channel,unit
   SO-90001,2026-11-26T01:00,kbd-0101,2,marketplace,each
   SO-90002,2026-11-26T01:01, HDS-0402 ,1,web,each
   SO-90003,2026-11-26T01:02,MON–0201,1,web,each
   SO-90004,2026-11-26T01:03,ＫＢＤ-0101,1,web,each
   SO-90005,2026-11-26T01:04,XYZ-9999,1,web,each
   SO-90006,2026-11-26T01:05,KBD-01O1,1,web,each
   EOF
   tail -n +2 data/orders.csv >> $T/orders.csv
   .venv/bin/python job.py --source api --orders $T/orders.csv --db $T/inventory.db --rejected $T/rej.csv; echo "exit=$?"; cat $T/rej.csv
   ```

   … 2 more lines of this command
14. ```text
   .venv/bin/python - <<'EOF'
   from pathlib import Path
   p=Path("README.md"); s=p.read_text()
   old="The job prints `sync finished: OK` and exits with code 0 when the sync is done. If it cannot run (no database, unreadable export), it prints `sync failed: ...` on stderr and exits with code 2."
   assert old in s
   s=s.replace(old, old+"""
   
   If some orders cannot be applied (a SKU not in the format `AAA-0000` or not in the inventory, a bad quantity or unit), the others are still applied, and the job prints `sync finished: N orders REJECTED (...)` on stderr and exits with code 1. The sales API does not hand an order over twice, so the rejected orders are kept in `data/rejected_orders.csv` (`--rejected PATH` for another file), in the export's format plus a `reason` column. Fix them there and replay them with `python3 job.py --orders data/rejected_orders.csv`.
   
   SKUs are normalized before they are checked: spaces around them are removed, letters are made upper case, and full-width characters and typographic dashes become plain ones.""")
   p.write_text(s)
   EOF
   ```

Its change, against `task/`

````text
--- task/README.md
+++ README.md
@@ -13,6 +13,10 @@
 ```
 
 The job prints `sync finished: OK` and exits with code 0 when the sync is done. If it cannot run (no database, unreadable export), it prints `sync failed: ...` on stderr and exits with code 2.
+
+If some orders cannot be applied (a SKU not in the format `AAA-0000` or not in the inventory, a bad quantity or unit), the others are still applied, and the job prints `sync finished: N orders REJECTED (...)` on stderr and exits with code 1. The sales API does not hand an order over twice, so the rejected orders are kept in `data/rejected_orders.csv` (`--rejected PATH` for another file), in the export's format plus a `reason` column. Fix them there and replay them with `python3 job.py --orders data/rejected_orders.csv`.
+
+SKUs are normalized before they are checked: spaces around them are removed, letters are made upper case, and full-width characters and typographic dashes become plain ones.
 
 Running the job again over the same orders is safe: an order is applied only once.
 
--- task/job.py
+++ job.py
@@ -9,6 +9,7 @@
 """
 
 import argparse
+import csv
 import logging
 import os
 import sys
@@ -21,6 +22,11 @@
 
 HERE = Path(__file__).resolve().parent
 DEFAULT_ORDERS = HERE / "data" / "orders.csv"
+# Orders that could not be applied. The sales API hands an order over only
+# once, so a rejected order is kept here (in the export's format) to be fixed
+# and replayed with: python3 job.py --orders data/rejected_orders.csv
+DEFAULT_REJECTED = HERE / "data" / "rejected_orders.csv"
+REJECTED_FIELDS = ("order_id", "placed_at", "sku", "quantity", "channel", "unit", "reason")
 
 log = logging.getLogger("order_sync")
 
@@ -47,17 +53,46 @@
 
 
 def sync_orders(conn, orders):
-    """Apply every order to the inventory. Returns how many were applied now."""
+    """Apply every order to the inventory.
+
+    Returns (applied, rejected): how many were applied now, and a list of
+    (order, reason) for the orders that break a rule or name an unknown SKU.
+    Any other error is not an order problem and stops the job.
+    """
     applied = 0
+    rejected = []
     for order in orders:
         try:
             validate.check_order(order)
             if inventory.apply_order(conn, order):
                 applied += 1
-        except Exception as exc:
-            log.warning("order %s skipped: %s", order.order_id, exc)
-            continue
-    return applied
+        except (validate.ValidationError, inventory.UnknownSkuError) as exc:
+            log.error("order %s rejected: %s", order.order_id, exc)
+            rejected.append((order, str(exc)))
+    return applied, rejected
+
+
+def save_rejected(path, rejected):
+    """Append the rejected orders to a CSV that job.py can read back."""
+    path = Path(path)
+    already = set()
+    if path.exists():
+        with open(path, newline="", encoding="utf-8") as handle:
+            already = {row["order_id"] for row in csv.DictReader(handle)}
+    new = [(o, reason) for o, reason in rejected if o.order_id not in already]
+    if not new:
+        return
+    path.parent.mkdir(parents=True, exist_ok=True)
+    write_header = not path.exists() or path.stat().st_size == 0
+    with open(path, "a", newline="", encoding="utf-8") as handle:
+        writer = csv.writer(handle)
+        if write_header:
+            writer.writerow(REJECTED_FIELDS)
+        for o, reason in new:
+            writer.writerow(
+                (o.order_id, o.placed_at.isoformat(timespec="minutes"), o.sku,
+                 o.quantity, o.channel, o.unit, reason)
+            )
 
 
 def main(argv=None):
@@ -65,6 +100,9 @@
     parser.add_argument("--source", choices=("csv", "api"), default="csv")
     parser.add_argument("--orders", default=DEFAULT_ORDERS, help="the CSV export")
     parser.add_argument("--db", default=inventory.DEFAULT_DB, help="the SQLite file")
+    parser.add_argument(
+        "--rejected", default=DEFAULT_REJECTED, help="where rejected orders are kept"
+    )
     args = parser.parse_args(argv)
     configure_logging()
 
@@ -75,9 +113,18 @@
         print(f"sync failed: {exc}", file=sys.stderr)
         return 2
 
-    applied = sync_orders(conn, orders)
+    applied, rejected = sync_orders(conn, orders)
     conn.close()
     log.info("%d orders read, %d applied in this run", len(orders), applied)
+    if rejected:
+        save_rejected(args.rejected, rejected)
+        ids = ", ".join(order.order_id for order, _ in rejected)
+        print(
+            f"sync finished: {len(rejected)} orders REJECTED ({ids}); "
+            f"kept in {args.rejected}",
+            file=sys.stderr,
+        )
+        return 1
     print("sync finished: OK")
     return 0
 
--- task/parse.py
+++ parse.py
@@ -1,7 +1,12 @@
 """Turn raw order rows into Order records."""
 
+import re
+import unicodedata
 from dataclasses import dataclass
 from datetime import datetime
+
+# Hyphen-like characters that should be read as "-" in a SKU.
+_DASHES = re.compile(r"[‐-―−﹘﹣－]")
 
 FIELDS = ("order_id", "placed_at", "sku", "quantity", "channel")
 # Optional column: "each" (single items, the default) or "pack".
@@ -22,6 +27,17 @@
     unit: str = DEFAULT_UNIT
 
 
+def normalize_sku(raw):
+    """Write a SKU the way the warehouse does: AAA-0000.
+
+    The sales system does not always send SKUs that way (lower case, stray
+    spaces, full-width characters, a typographic dash). Without this, those
+    orders fail the SKU check and never reach the inventory.
+    """
+    sku = unicodedata.normalize("NFKC", raw).strip().upper()
+    return _DASHES.sub("-", sku)
+
+
 def parse_row(row):
     """Build one Order from a mapping with the columns in FIELDS."""
     missing = [name for name in FIELDS if row.get(name) in (None, "")]
@@ -35,7 +51,7 @@
     return Order(
         order_id=row["order_id"].strip(),
         placed_at=placed_at,
-        sku=row["sku"],
+        sku=normalize_sku(row["sku"]),
         quantity=quantity,
         channel=row["channel"].strip(),
         unit=(row.get("unit") or DEFAULT_UNIT).strip().lower(),
````

What the check said

```text
pass  orders with a SKU in a bad format: exit 0, said OK: True, stock that is not the count: none
pass  the same orders, well formed: exit 0, said OK: True, stock that is not the count: none
fixed
```

## Every run

The first attempt of every run of every arm.

| Arm | Run | Check | Last line | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|
| `none` | 1 | passed | `fixed` | 10 | 208,668 | 93 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-none-1.jsonl) |
| `none` | 2 | passed | `fixed` | 9 | 180,866 | 81 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-none-2.jsonl) |
| `none` | 3 | passed | `fixed` | 17 | 53,451 | 757 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-none-3.jsonl) |
| `raw` | 1 | passed | `fixed` | 13 | 376,322 | 88 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-raw-1.jsonl) |
| `raw` | 2 | passed | `fixed` | 17 | 325,948 | 100 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-raw-2.jsonl) |
| `raw` | 3 | passed | `fixed` | 10 | 171,702 | 63 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-raw-3.jsonl) |
| `ormaos` | 1 | passed | `fixed` | 14 | 300,076 | 94 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-ormaos-1.jsonl) |
| `ormaos` | 2 | passed | `fixed` | 14 | 348,376 | 90 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-ormaos-2.jsonl) |
| `ormaos` | 3 | passed | `fixed` | 13 | 254,030 | 70 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/order-sync-ormaos-3.jsonl) |

## The results files

- The benchmark: [fix](https://ormaos.com/benchmarks/fix/)
- Results folder: [`agent-bench/results/20261126-220703`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703): 2026-11-26, `claude-code / claude-opus-5-5`, bubblewrap, network open
