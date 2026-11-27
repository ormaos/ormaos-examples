# order-sync, in knows2

*Situation · knows2*

A scheduled job. A scheduled job that applies the new orders of a sales system to a warehouse inventory. Source: [`order-sync`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/order-sync).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Mean score over every run: `none` 0.38, `raw` 1.00, `ormaos` 0.92, `ormaos-values` 1.00 (3 runs per arm). Agent: `claude-code / claude-opus-5-5`.

## What happened

The job parsed 26 orders from the sales API: 19 were applied, 2 had been applied by an earlier run, and 5 were skipped after an exception (`SkuFormatError`): `SO-20521`, `SO-20526`, `SO-20530`, `SO-20533` and `SO-20537`. It took 104 items out of stock, inserted 2 back-order rows for 5 items, and printed `sync finished: OK`.

The numbers are the oracle's answers to the questions below: [`oracle/order-sync.json`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/oracle/order-sync.json).

## What the agent was given

The folder the execution left, with what the arm adds, and 8 questions in `questions.json`, written by a model that was not told about Ormaos. The oracle's answers were not in the folder.

| Question | Asked | Format | The oracle's answer |
|---|---|---|---|
| q1 | How many order rows did the sales API's GET /orders return to the job in this run (the number of orders parsed, len(orders) in job.main)? | A non-negative integer, e.g. 42 | `26` |
| q2 | How many orders were newly applied to the inventory in this run, i.e. for how many orders did inventory.apply_order return True and insert a row into applied_orders? | A non-negative integer, e.g. 37 | `19` |
| q3 | How many orders were passed over without error because an earlier run had already applied their order_id (inventory.apply_order returned False)? | A non-negative integer, e.g. 3 | `2` |
| q4 | How many orders were skipped because an exception was raised for them inside sync_orders (validation failure, unknown SKU, or any other error), each of which produced an 'order ... skipped' warning that the default ERROR log level suppressed? | A non-negative integer, e.g. 2 | `5` |
| q5 | What are the order_ids of the orders skipped because of an exception in sync_orders (the orders counted in q4)? | A JSON list of order_id strings sorted in ascending lexicographic order, e.g. ["A-1007", "A-1012"]; [] if none | `["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"]` |
| q6 | For each skipped order (the orders counted in q4), which exception class caused it to be skipped? | A JSON object mapping each skipped order_id to the exception class name, e.g. {"A-1007": "SkuFormatError", "A-1012": "UnknownSkuError"}; {} if none | `{"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"}` |
| q7 | How many single items in total were taken out of stock in this run, i.e. the sum of the 'taken' quantity over all orders newly applied in this run (after pack-to-item conversion and capping at the stock on hand)? | A non-negative integer, e.g. 318 | `104` |
| q8 | How many back-order rows did this run insert into the backorders table, and how many items did they add up to in total? | Two non-negative integers separated by a comma: rows,items, e.g. 2,15 | `[2, 5]` |

**The prompt of each arm, verbatim**

`none`:

```text
Last night cron ran `python3 job.py --source api` in this folder; since then the sales system has replaced its orders with today's. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
Last night cron ran `python3 job.py --source api` in this folder; since then the sales system has replaced its orders with today's. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
Last night cron ran `python3 job.py --source api` in this folder; since then the sales system has replaced its orders with today's. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
Last night cron ran `python3 job.py --source api` in this folder; since then the sales system has replaced its orders with today's. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the lines of its output that hold a value the agent wrote in `answers.json`, or its first 15 lines, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-none-1.jsonl)
- Score 0.38: 3 right, 5 null, 0 wrong
- 4 tool calls, 73,237 tokens, 42 s

Commands, in order (4):

1. ```text
   cd /srv/order-sync; ls -la; cat questions.json; cat job.py
   ```
2. ```text
   cd /srv/order-sync; cat README.md fetch.py inventory.py parse.py validate.py; ls -la data
   ```
3. ```text
   cd /srv/order-sync/data; cat cron.log; echo; cat orders.csv; echo; cat count.csv; echo; for t in stock applied_orders backorders; do echo "== $t"; sqlite3 inventory.db "select * from $t" 2>&1 || python3 -I -c "import sqlite3;c=sqlite3.connect('inventory.db');[print(r) for r in c.execute('select * from $t')]"; done; ls -la ~ /srv/order-sync/.ormaos 2>&1
   ```
4. ```text
   cd /srv/order-sync; cat > answers.json <<'EOF'
   {
     "q1": null,
     "q2": 19,
     "q3": null,
     "q4": null,
     "q5": null,
     "q6": null,
     "q7": 104,
     "q8": "2,5"
   }
   EOF
   ```

   … 1 more line of this command

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | null |  |
| q2 | right | `19` |
| q3 | null |  |
| q4 | null |  |
| q5 | null |  |
| q6 | null |  |
| q7 | right | `104` |
| q8 | right | `"2,5"` |

Its own words on q1, q3, q4, q5 and q6: the paragraphs of its last message that name them

```text
**Answers:**
- **q2 = 19:** the 19 orders stamped at :44.
- **q7 = 104:** the total of the `quantity` (items taken) on those 19 rows.
- **q8 = "2,5":** both back-orders belong to orders stamped at :44: SO-20524 (2 items) and SO-20534 (3 items).
- **q1, q3, q4, q5, q6 = null:** these need the list of orders the API returned, which was overwritten. SO-20521, 20526, 20530, 20533 and 20537 are missing from `applied_orders`, so they were probably skipped. But I can't tell which run received them or what error each hit. I also can't tell how many already-applied orders came in again. Some stock levels don't match `data/count.csv` (KBD-0101 is 9 higher than the count, MON-0201 is 1 higher, HDS-0402 is 4 higher). That fits orders being dropped silently, but it isn't enough to answer these questions.
```

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-raw-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 9 tool calls, 268,235 tokens, 70 s

Commands, in order (9):

1. ```text
   cd /srv/order-sync; ls -la; cat questions.json; cat job.py; ls -R | head -50
   ```
2. ```text
   cd /srv/order-sync; cat README.md fetch.py inventory.py parse.py validate.py; cat data/cron.log | tail; head -3 data/count.csv; wc -l data/*.csv
   ```
3. ```text
   cd /srv/order-sync; cat data/cron.log; python3 -I -c "
   import json,collections
   d=json.load(open('result.json'))
   ev=d['traceEvents']; print(len(ev)); print(d.keys()); print(ev[0]); 
   c=collections.Counter(e.get('name') for e in ev)
   for n,k in c.most_common():
     if any(s in n for s in ['job.py','inventory.py','validate.py','parse.py','fetch.py','Error','execute']): print(k,n)
   print([e for e in ev if 'args' in e][:5])
   "
   ```
4. ```text
   cd /srv/order-sync; cat data/orders.csv; sqlite3 data/inventory.db "select * from stock; select * from applied_orders order by applied_at; select * from backorders;" 2>&1 || python3 -I -c "
   import sqlite3;c=sqlite3.connect('data/inventory.db')
   for t in ['stock','applied_orders','backorders']:
     print(t)
     for r in c.execute(f'select * from {t}'): print(r)"
   ```
5. ```text
   cd /srv/order-sync; python3 -I -c "
   import json
   d=json.load(open('result.json'))
   print(d['viztracer_metadata'])
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X']
   ev.sort(key=lambda e:e['ts'])
   print(ev[0]['ts'], ev[-1]['ts'])
   sel=[e for e in ev if any(s in e['name'] for s in ['apply_order','check_','to_units','execute','sync_orders','fetchone','Error','warning','isEnabledFor','datetime','now'])]
   for e in sel: print(e['ts'],e['dur'],e['name'])
   " | head -300
   ```
6. ```text
   cd /srv/order-sync; python3 -I -c "
   import json
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X' and e.get('tid')==2]
   ev.sort(key=lambda e:(e['ts'],-e['dur']))
   s=[e for e in ev if e['name'].startswith('sync_orders')][0]
   inner=[e for e in ev if s['ts']<=e['ts']<=s['ts']+s['dur']]
   seq=[]
   for co in [e for e in inner if e['name'].startswith('check_order')]:
     pass
   ao=[e for e in inner if e['name'].startswith('apply_order')]
   cos=[e for e in inner if e['name'].startswith('check_order')]
   ```

   … 14 more lines of this command
7. ```text
   cd /srv/order-sync; python3 -I -c "
   import json
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X' and e.get('tid')==2]
   ev.sort(key=lambda e:(e['ts'],-e['dur']))
   s=[e for e in ev if e['name'].startswith('sync_orders')][0]
   inner=[e for e in ev if s['ts']<e['ts']<=s['ts']+s['dur']]
   for e in inner:
     if e['name'].split(' ')[0] in ('check_order','apply_order','Logger.warning','to_units','check_sku','check_quantity','check_unit') or 'Error' in e['name'] or 'execute' in e['name']: print(round(e['ts']-s['ts'],1), e['name'].split(' ')[0])
   " | awk '{print \$2}' | tr '\n' ' ' | sed 's/check_order/\n&/g'
   ```
8. ```text
   cd /srv/order-sync; python3 -I -c "
   import json
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X' and e.get('tid')==2]
   ev.sort(key=lambda e:(e['ts'],-e['dur']))
   s=[e for e in ev if e['name'].startswith('sync_orders')][0]
   inner=[e for e in ev if s['ts']<e['ts']<=s['ts']+s['dur']]
   out=[]
   for e in inner:
     n=e['name'].split(' ')[0]
     if n=='check_order': out.append('\n')
     out.append({'sqlite3.Connection.execute':'X'}.get(n,n))
   ```

   … 2 more lines of this command
9. ```text
   cd /srv/order-sync; cat > answers.json <<'EOF'
   {
     "q1": 26,
     "q2": 19,
     "q3": 2,
     "q4": 5,
     "q5": ["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"],
     "q6": {"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"},
     "q7": 104,
     "q8": "2,5"
   }
   EOF
   ```

   … 1 more line of this command

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `26` |
| q2 | right | `19` |
| q3 | right | `2` |
| q4 | right | `5` |
| q5 | right | `["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"]` |
| q6 | right | `{"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"}` |
| q7 | right | `104` |
| q8 | right | `"2,5"` |

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 6 tool calls, 145,676 tokens, 52 s

Commands, in order (6):

1. ```text
   ls -la && cat questions.json && .venv/bin/ormaos guide
   ```

   Output, the first 15 of 182 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-1.jsonl?plain=1#L4)):

   ```text
   total 52
   drwxrwxr-x 5 levimbraga levimbraga 4096 Nov 27 16:57 .
   drwx------ 3 levimbraga levimbraga   60 Nov 27 17:03 ..
   drwxrwxr-x 3 levimbraga levimbraga 4096 Nov 27 16:57 .ormaos
   drwxrwxr-x 5 levimbraga levimbraga 4096 Nov 27 16:57 .venv
   -rw-rw-r-- 1 levimbraga levimbraga 4104 Nov 13 10:41 README.md
   drwxrwxr-x 2 levimbraga levimbraga 4096 Nov 27 16:57 data
   -rw-rw-r-- 1 levimbraga levimbraga 2227 Nov 13 10:41 fetch.py
   -rw-rw-r-- 1 levimbraga levimbraga 5822 Nov 13 10:39 inventory.py
   -rw-rw-r-- 1 levimbraga levimbraga 2607 Nov 11 13:16 job.py
   -rw-rw-r-- 1 levimbraga levimbraga 1425 Nov 13 10:39 parse.py
   -rw-rw-r-- 1 levimbraga levimbraga 2319 Nov 27 16:57 questions.json
   -rw-rw-r-- 1 levimbraga levimbraga 1236 Nov 13 10:39 validate.py
   {
     "questions": [
   ```
2. ```text
   cat job.py inventory.py parse.py validate.py fetch.py; ls data; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the 3 lines of 483 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-1.jsonl?plain=1#L6)):

   ```text
   class SkuFormatError(ValidationError):
           raise SkuFormatError(f"SKU {sku!r} is not in the format AAA-0000")
   not collected: io: reads of the 1 file opened at fetch.py:26: opened for reading, and no `read` call by Python code was seen on a file of that name: if it was read, that was inside C code (a file that is iterated, `for line in f`, `csv.reader`)
   ```
3. ```text
   O=.venv/bin/ormaos; $O exceptions r1; $O io r1; $O logs r1 --dropped; $O tree r1 --depth 3; cat data/cron.log
   ```

   Output, the 6 lines of 60 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-1.jsonl?plain=1#L12)):

   ```text
     1x file open data/orders.csv (read)  at fetch.py:26 in from_csv  [r1:i3]
       r1:c13 SkuFormatError() -> NoneType  validate.py:14  5us
       r1:c19 load_orders(source: str[3], orders_csv: pathlib.PosixPath) -> list[26 parse.Order]  job.py:37  515.4ms  io 1  logs 1  calls below: 3
         r1:c23 from_api(base_url: str[22]) -> list[26 dict]  fetch.py:30  9.1ms  io 1
         r1:c27 parse_rows(rows: list[26 dict]) -> list[26 parse.Order]  parse.py:45  3.2ms  calls below: 52
       r1:c106 sync_orders(conn: sqlite3.Connection, orders: list[26 parse.Order]) -> int  job.py:49  18.5ms  io 120  logs 5  [swallowed 5x validate.SkuFormatError: r1:e1]  calls below: 47
   ```
4. ```text
   python3 -I -c "
   import sqlite3;c=sqlite3.connect('file:data/inventory.db?mode=ro',uri=True)
   for t in ['stock','applied_orders','backorders']:
     print(t);[print(r) for r in c.execute(f'select * from {t}')]
   "; head -5 data/orders.csv; wc -l data/orders.csv; ls -la --time-style=full-iso data .ormaos .ormaos/*
   ```
5. ```text
   .venv/bin/ormaos tree r1:c106 --depth 1 --limit 100 | grep -E "check_order|apply_order" | awk '{print $2, $3, $NF, $(NF-1)}' | nl | head -60; cat data/count.csv
   ```

   Output, the 2 lines of 56 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-1.jsonl?plain=1#L31)):

   ```text
       19	apply_order(conn: sqlite3.Connection, 1 below:
       26	check_order(order: parse.Order) 1 below:
   ```
6. ```text
   cat > answers.json <<'EOF'
   {
     "q1": 26,
     "q2": 19,
     "q3": 2,
     "q4": 5,
     "q5": ["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"],
     "q6": {"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"},
     "q7": 104,
     "q8": "2,5"
   }
   EOF
   ```

   … 1 more line of this command

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `26` |
| q2 | right | `19` |
| q3 | right | `2` |
| q4 | right | `5` |
| q5 | right | `["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"]` |
| q6 | right | `{"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"}` |
| q7 | right | `104` |
| q8 | right | `"2,5"` |

#### `ormaos-values`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-values-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 7 tool calls, 183,154 tokens, 47 s

Commands, in order (7):

1. ```text
   ls -la && cat questions.json && .venv/bin/ormaos guide
   ```

   Output, the first 15 of 182 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-values-1.jsonl?plain=1#L5)):

   ```text
   total 52
   drwxrwxr-x 5 levimbraga levimbraga 4096 Nov 27 16:57 .
   drwx------ 3 levimbraga levimbraga   60 Nov 27 17:03 ..
   drwxrwxr-x 3 levimbraga levimbraga 4096 Nov 27 16:57 .ormaos
   drwxrwxr-x 5 levimbraga levimbraga 4096 Nov 27 16:57 .venv
   -rw-rw-r-- 1 levimbraga levimbraga 4104 Nov 13 10:41 README.md
   drwxrwxr-x 2 levimbraga levimbraga 4096 Nov 27 16:57 data
   -rw-rw-r-- 1 levimbraga levimbraga 2227 Nov 13 10:41 fetch.py
   -rw-rw-r-- 1 levimbraga levimbraga 5822 Nov 13 10:39 inventory.py
   -rw-rw-r-- 1 levimbraga levimbraga 2607 Nov 11 13:16 job.py
   -rw-rw-r-- 1 levimbraga levimbraga 1425 Nov 13 10:39 parse.py
   -rw-rw-r-- 1 levimbraga levimbraga 2319 Nov 27 16:57 questions.json
   -rw-rw-r-- 1 levimbraga levimbraga 1236 Nov 13 10:39 validate.py
   {
     "questions": [
   ```
2. ```text
   cat job.py inventory.py validate.py parse.py fetch.py; ls data; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the 3 lines of 484 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-values-1.jsonl?plain=1#L8)):

   ```text
   class SkuFormatError(ValidationError):
           raise SkuFormatError(f"SKU {sku!r} is not in the format AAA-0000")
   not collected: io: reads of the 1 file opened at fetch.py:26: opened for reading, and no `read` call by Python code was seen on a file of that name: if it was read, that was inside C code (a file that is iterated, `for line in f`, `csv.reader`)
   ```
3. ```text
   O=.venv/bin/ormaos; $O exceptions r1; $O tree r1 --function apply_order --limit 100; $O tree r1 --function sync_orders; $O tree r1 --function parse_rows; $O io r1 --limit 200
   ```

   Output, the 3 lines of 49 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-values-1.jsonl?plain=1#L13)):

   ```text
   r1:c106 sync_orders(conn: sqlite3.Connection, orders: list[26 parse.Order]) -> int=19  job.py:49  22.1ms  io 120  logs 5  [swallowed 5x validate.SkuFormatError: r1:e1]  calls below: 47
   r1:c27 parse_rows(rows: list[26 dict]="[{\"order_id\": \"SO-20513\", \"placed_at\": \"2026-11-25T17:26\"...") -> list[26 parse.Order]  parse.py:45  7.2ms  calls below: 52
     1x file open data/orders.csv (read)  at fetch.py:26 in from_csv  [r1:i3]
   ```
4. ```text
   O=.venv/bin/ormaos; $O tree r1:c106 --limit 100 | head -80; $O exceptions r1:e1; cat data/cron.log | tail -20
   ```

   Output, the 1 line of 90 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-values-1.jsonl?plain=1#L20)):

   ```text
   r1:c106 sync_orders(conn: sqlite3.Connection, orders: list[26 parse.Order]) -> int=19  job.py:49  22.1ms  io 120  logs 5  [swallowed 5x validate.SkuFormatError: r1:e1]  calls below: 47
   ```
5. ```text
   cat data/cron.log; python3 -I -c "
   import sqlite3;c=sqlite3.connect('file:data/inventory.db?mode=ro',uri=True)
   for t in ['stock','applied_orders','backorders']:
     print(t)
     for r in c.execute(f'select * from {t}'): print(r)
   "; head -3 data/orders.csv; wc -l data/orders.csv
   ```
6. ```text
   O=.venv/bin/ormaos; $O tree r1 --function parse_row --limit 100 | grep -oE 'SO-205(21|26|30|33|37)[^}]*' ; $O tree r1 --function check_sku | grep raised; $O exceptions r1 --json | python3 -I -c "import json,sys;d=json.load(sys.stdin);print(json.dumps(d)[:3000])"
   ```

   Output, the 6 lines of 12 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-values-1.jsonl?plain=1#L34)):

   ```text
   SO-20521\", \"placed_at\": \"2026-11-26T10:36\",...") -> parse.Order  parse.py:25  194us  calls below: 1
   SO-20526\", \"placed_at\": \"2026-11-26T13:10\",...") -> parse.Order  parse.py:25  201us  calls below: 1
   SO-20530\", \"placed_at\": \"2026-11-26T15:38\",...") -> parse.Order  parse.py:25  201us  calls below: 1
   SO-20533\", \"placed_at\": \"2026-11-26T17:24\",...") -> parse.Order  parse.py:25  186us  calls below: 1
   SO-20537\", \"placed_at\": \"2026-11-26T20:02\",...") -> parse.Order  parse.py:25  177us  calls below: 1
   r1: 26 of the 240 calls match --function check_sku (26 check_sku; 5 raised)
   ```
7. ```text
   cat > answers.json <<'EOF'
   {
     "q1": 26,
     "q2": 19,
     "q3": 2,
     "q4": 5,
     "q5": ["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"],
     "q6": {"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"},
     "q7": 104,
     "q8": "2,5"
   }
   EOF
   ```

   … 1 more line of this command

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `26` |
| q2 | right | `19` |
| q3 | right | `2` |
| q4 | right | `5` |
| q5 | right | `["SO-20521", "SO-20526", "SO-20530", "SO-20533", "SO-20537"]` |
| q6 | right | `{"SO-20521": "SkuFormatError", "SO-20526": "SkuFormatError", "SO-20530": "SkuFormatError", "SO-20533": "SkuFormatError", "SO-20537": "SkuFormatError"}` |
| q7 | right | `104` |
| q8 | right | `"2,5"` |

## What Ormaos data answered

Read from the streams: in each run of an Ormaos arm, the `ormaos` verbs in its commands up to its last write of `answers.json`. A question counts for a verb when a run that ran the verb answered it (not null); a run that ran several verbs counts under each of them.

| Question | `ormaos`: verbs (runs) | answered | right | `ormaos-values`: verbs (runs) | answered | right |
|---|---|---|---|---|---|---|
| q1 | show 3, tree 3, exceptions 3, io 3, logs 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3, help 1 | 3/3 | 3/3 |
| q2 | show 3, tree 3, exceptions 3, io 3, logs 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3, help 1 | 3/3 | 3/3 |
| q3 | show 3, tree 3, exceptions 3, io 3, logs 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3, help 1 | 3/3 | 3/3 |
| q4 | show 3, tree 3, exceptions 3, io 3, logs 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3, help 1 | 3/3 | 3/3 |
| q5 | show 2, tree 2, exceptions 2, io 2, logs 2, list 2, guide 2 | 2/3 | 2/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3, help 1 | 3/3 | 3/3 |
| q6 | show 2, tree 2, exceptions 2, io 2, logs 2, list 2, guide 2 | 2/3 | 2/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3, help 1 | 3/3 | 3/3 |
| q7 | show 3, tree 3, exceptions 3, io 3, logs 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3, help 1 | 3/3 | 3/3 |
| q8 | show 3, tree 3, exceptions 3, io 3, logs 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3, help 1 | 3/3 | 3/3 |

## Every run

Every run of every arm.

| Arm | Run | Score | Right | Null | Wrong | `ormaos` verbs before answers.json | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` | 1 | 0.38 | 3 | 5 | 0 | – | 4 | 73,237 | 42 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-none-1.jsonl) |
| `none` | 2 | 0.38 | 3 | 5 | 0 | – | 4 | 73,893 | 41 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-none-2.jsonl) |
| `none` | 3 | 0.38 | 3 | 5 | 0 | – | 4 | 75,542 | 48 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-none-3.jsonl) |
| `raw` | 1 | 1.00 | 8 | 0 | 0 | – | 9 | 268,235 | 70 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-raw-1.jsonl) |
| `raw` | 2 | 1.00 | 8 | 0 | 0 | – | 6 | 182,999 | 55 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-raw-2.jsonl) |
| `raw` | 3 | 1.00 | 8 | 0 | 0 | – | 5 | 157,322 | 51 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-raw-3.jsonl) |
| `ormaos` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, exceptions, io, logs, tree | 6 | 145,676 | 52 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-1.jsonl) |
| `ormaos` | 2 | 0.75 | 6 | 2 | 0 | guide, list, show, exceptions, io, logs, tree | 7 | 185,219 | 61 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-2.jsonl) |
| `ormaos` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, exceptions, io, tree, logs | 6 | 155,911 | 54 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-3.jsonl) |
| `ormaos-values` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, exceptions, tree, io | 7 | 183,154 | 47 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-values-1.jsonl) |
| `ormaos-values` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, exceptions, tree, io | 8 | 255,162 | 59 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-values-2.jsonl) |
| `ormaos-values` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, exceptions, io, tree, help | 9 | 272,558 | 56 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/order-sync-ormaos-values-3.jsonl) |

## The results files

- The benchmark: [knows2](https://ormaos.com/benchmarks/knows2/#order-sync)
- Results folder: [`agent-bench/knows2/results/20261127-165801`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801)
