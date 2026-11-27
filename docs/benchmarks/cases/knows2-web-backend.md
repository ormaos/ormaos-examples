# web-backend, in knows2

*Situation · knows2*

A web backend. A FastAPI service over a SQLite database of customers, products and orders, with one route that lists a customer's orders, each with its total. Source: [`use-cases/web-backend`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/web-backend).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Mean score over every run: `none` 1.00, `raw` 1.00, `ormaos` 0.96, `ormaos-values` 1.00 (3 runs per arm). Agent: `claude-code / claude-opus-5-5`.

## What happened

During the one request that `main.py` made, the route answered with the customer `Clara` and orders whose `total_cents` add up to 18200; the largest is order 8, with 3660. Handling it ran 38 SQL statements and called `price_of` 24 times; `discount_for` returned 0, from its `except KeyError` branch. Before the request, `store.create()` inserted 38 rows into `order_items`.

The numbers are the oracle's answers to the questions below: [`oracle/web-backend.json`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/oracle/web-backend.json).

## What the agent was given

The folder the execution left, with what the arm adds, and 8 questions in `questions.json`, written by a model that was not told about Ormaos. The oracle's answers were not in the folder.

| Question | Asked | Format | The oracle's answer |
|---|---|---|---|
| q1 | What customer name did the route put in the "customer" field of the response body it returned for this request? | A single name exactly as stored in the database, e.g. "Name" | `"Clara"` |
| q2 | What discount percentage did discount_for return for the requested customer during this request, and was it reached through the except KeyError branch? | An integer followed by yes or no, e.g. "7, no" | `[0, true]` |
| q3 | What was the id of the first order in the "orders" list of the response? | An integer | `8` |
| q4 | What was the sum of the "total_cents" values across all orders in the response? | An integer number of cents | `18200` |
| q5 | Which order in the response had the largest "total_cents", and what was that value? | Order id and total, as "id, cents" (two integers) | `[8, 3660]` |
| q6 | How many times was price_of called while the request was handled? | An integer | `24` |
| q7 | In total, how many SQL statements were run with db.execute on the request's database connection while list_orders handled the request (counting find_customer, the orders query, items_of, price_of and product_names calls)? | An integer | `38` |
| q8 | How many rows did store.create() insert into the order_items table when it rebuilt orders.db before the request? | An integer | `38` |

**The prompt of each arm, verbatim**

`none`:

```text
`.venv/bin/python main.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
`.venv/bin/python main.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
`.venv/bin/python main.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
`.venv/bin/python main.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the lines of its output that hold a value the agent wrote in `answers.json`, or its first 15 lines, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-none-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 4 tool calls, 49,569 tokens, 25 s

Commands, in order (4):

1. ```text
   cd /srv/web-backend; ls -la; cat questions.json; cat main.py
   ```
2. ```text
   cd /srv/web-backend; cat app.py store.py README.md requirements.txt
   ```
3. ```text
   cd /srv/web-backend; python3 -I -c "
   import sqlite3
   c=sqlite3.connect('orders.db')
   print(c.execute('select * from customers').fetchall())
   print(c.execute('select * from products').fetchall())
   print(c.execute('select count(*) from order_items').fetchall())
   os=c.execute('select id,placed from orders where customer_id=3 order by placed').fetchall()
   print(os)
   tot=[];calls=0;ex=2
   for o,p in os:
     its=c.execute('select product_id,quantity from order_items where order_id=?',(o,)).fetchall(); ex+=1
     t=0
   ```

   … 5 more lines of this command
4. ```text
   cd /srv/web-backend; cat > answers.json <<'E'
   {"q1": "Clara", "q2": "0, yes", "q3": 8, "q4": 18200, "q5": "8, 3660", "q6": 24, "q7": 38, "q8": 38}
   E
   cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `"Clara"` |
| q2 | right | `"0, yes"` |
| q3 | right | `8` |
| q4 | right | `18200` |
| q5 | right | `"8, 3660"` |
| q6 | right | `24` |
| q7 | right | `38` |
| q8 | right | `38` |

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-raw-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 5 tool calls, 72,462 tokens, 36 s

Commands, in order (5):

1. ```text
   cd /srv/web-backend; ls -la; cat questions.json; python3 -c "
   import json;d=json.load(open('result.json'));e=d['traceEvents'];print(len(e));print(e[:3])"
   ```
2. ```text
   cd /srv/web-backend; cat README.md app.py main.py store.py requirements.txt
   ```
3. ```text
   cd /srv/web-backend; python3 -c "
   import json,collections;d=json.load(open('result.json'));e=d['traceEvents']
   c=collections.Counter(x['name'] for x in e if 'app.py' in x.get('name','') or 'store.py' in x.get('name','') or 'main.py' in x.get('name',''))
   for k,v in c.items():print(v,k)
   for x in e:
     if any(s in x.get('name','') for s in ['list_orders','discount_for','find_customer','main.py']): print(x)
   print([k for k in d if k!='traceEvents'])
   " | head -50
   ```
4. ```text
   cd /srv/web-backend; python3 -c "
   import sqlite3;c=sqlite3.connect('orders.db')
   print(c.execute('select * from customers').fetchall())
   print(c.execute('select * from products').fetchall())
   print(c.execute('select count(*) from order_items').fetchall())
   r=[]
   for oid,pl in c.execute('select id,placed from orders where customer_id=3 order by placed').fetchall():
     t=sum(c.execute('select cents from products where id=?',(p,)).fetchone()[0]*q for p,q in c.execute('select product_id,quantity from order_items where order_id=?',(oid,)))
     r.append((oid,t))
   print(r,sum(t for _,t in r),max(r,key=lambda x:x[1]))
   "
   python3 -c "
   ```

   … 5 more lines of this command
5. ```text
   cd /srv/web-backend; cat > answers.json <<'E'
   {"q1": "Clara", "q2": "0, yes", "q3": 8, "q4": 18200, "q5": "8, 3660", "q6": 24, "q7": 38, "q8": 38}
   E
   cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `"Clara"` |
| q2 | right | `"0, yes"` |
| q3 | right | `8` |
| q4 | right | `18200` |
| q5 | right | `"8, 3660"` |
| q6 | right | `24` |
| q7 | right | `38` |
| q8 | right | `38` |

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 5 tool calls, 94,507 tokens, 28 s

Commands, in order (5):

1. ```text
   cd /srv/web-backend; ls -la; cat questions.json; .venv/bin/ormaos guide
   ```

   Output, the first 15 of 181 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-1.jsonl?plain=1#L4)):

   ```text
   total 56
   drwxrwxr-x 4 levimbraga levimbraga  4096 Nov 27 16:56 .
   drwx------ 3 levimbraga levimbraga    60 Nov 27 16:58 ..
   drwxrwxr-x 3 levimbraga levimbraga  4096 Nov 27 16:56 .ormaos
   drwxrwxr-x 5 levimbraga levimbraga  4096 Nov 27 13:56 .venv
   -rw-rw-r-- 1 levimbraga levimbraga   802 Nov 27 13:20 README.md
   -rw-rw-r-- 1 levimbraga levimbraga  2102 Nov 27 13:19 app.py
   -rw-rw-r-- 1 levimbraga levimbraga   523 Nov 27 13:19 main.py
   -rw-r--r-- 1 levimbraga levimbraga 20480 Nov 27 16:56 orders.db
   -rw-rw-r-- 1 levimbraga levimbraga  1729 Nov 27 16:56 questions.json
   -rw-rw-r-- 1 levimbraga levimbraga    27 Nov 27 13:19 requirements.txt
   -rw-rw-r-- 1 levimbraga levimbraga  1705 Nov 27 13:19 store.py
   {
     "questions": [
       {
   ```
2. ```text
   cd /srv/web-backend; cat main.py app.py store.py README.md; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the 1 line of 214 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-1.jsonl?plain=1#L6)):

   ```text
   CUSTOMERS = [(1, "Ana", "gold"), (2, "Bruno", "silver"), (3, "Clara", "trial")]
   ```
3. ```text
   cd /srv/web-backend; .venv/bin/ormaos io r1; .venv/bin/ormaos tree r1 --depth 4 | head -60; .venv/bin/ormaos tree r1 --function price_of | tail -5; .venv/bin/ormaos exceptions r1
   ```

   Output, the 1 line of 60 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-1.jsonl?plain=1#L12)):

   ```text
   r1:c10 list_orders(customer_id: int, names: bool, db: sqlite3.Connection) -> dict[2]  app.py:53  3.2ms  io 38  thread 2  calls below: 14
   ```
4. ```text
   cd /tmp && python3 -I -c "
   import sqlite3
   c=sqlite3.connect('file:/srv/web-backend/orders.db?mode=ro',uri=True)
   print(c.execute('select * from customers where id=3').fetchall())
   os=c.execute('select id,placed from orders where customer_id=3 order by placed').fetchall()
   tot=[]
   for i,p in os:
     t=sum(c.execute('select cents from products where id=?',(pid,)).fetchone()[0]*q for pid,q in c.execute('select product_id,quantity from order_items where order_id=?',(i,)).fetchall())
     tot.append((i,p,t))
   print(tot, sum(t for _,_,t in tot), max(tot,key=lambda x:x[2]))
   print(c.execute('select count(*) from order_items').fetchone())
   "
   ```
5. ```text
   Write answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `"Clara"` |
| q2 | right | `"0, yes"` |
| q3 | right | `8` |
| q4 | right | `18200` |
| q5 | right | `"8, 3660"` |
| q6 | right | `24` |
| q7 | right | `38` |
| q8 | right | `38` |

#### `ormaos-values`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-values-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 6 tool calls, 120,101 tokens, 32 s

Commands, in order (6):

1. ```text
   .venv/bin/ormaos guide; cat questions.json; ls -la
   ```

   Output, the first 15 of 181 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-values-1.jsonl?plain=1#L4)):

   ```text
   ormaos: what actually happened inside a Python execution.
   It records a run and shows it. It does not judge: you decide whether what
   happened is what should have happened.
   
   WHAT ORMAOS ANSWERS
   - What ran: the calls of the project's code, as a tree, with the shape of
     each argument and result (`orders: list[36 Order]`), never the values.
   - How often: counts by function, by line of code, by kind of I/O.
   - What was raised and caught: every exception, where it was raised and where
     it was handled. "swallowed" = it entered an `except` and was not raised
     again. Also "uncaught", "replaced", "exit".
   - What I/O happened: SQL statements, files, subprocesses, HTTP requests, each
     with the line of the project's code that caused it.
   - What was logged: `logging` records by level, logger and message template,
     with the line that asked for each; also the ones the level dropped.
   ```
2. ```text
   cat README.md app.py main.py store.py; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the 1 line of 215 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-values-1.jsonl?plain=1#L6)):

   ```text
   CUSTOMERS = [(1, "Ana", "gold"), (2, "Bruno", "silver"), (3, "Clara", "trial")]
   ```
3. ```text
   .venv/bin/ormaos tree r1 --limit 200; .venv/bin/ormaos io r1 --limit 200 | head -80; .venv/bin/ormaos exceptions r1:e1; .venv/bin/ormaos logs r1 --dropped
   ```

   Output, the 2 lines of 75 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-values-1.jsonl?plain=1#L11)):

   ```text
   r1:c10 list_orders(customer_id: int=3, names: bool=False, db: sqlite3.Connection) -> dict[2]="{\"customer\": \"Clara\", \"orders\": \"<another type>\"}"  app.py:53  3.3ms  io 38  thread 2  calls below: 14
     r1:c13 order_total(db: sqlite3.Connection, order_id: int=8) -> int=3660  app.py:49  353us  io 4  thread 2  calls below: 2
   ```
4. ```text
   .venv/bin/ormaos tree r1 --function price_of --limit 100 | tail -5; .venv/bin/ormaos tree r1 --function price_of --json | python3 -c "import sys,json;d=json.load(sys.stdin);print(list(d.keys()))"
   ```

   Output, all 6 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-values-1.jsonl?plain=1#L18)):

   ```text
   r1:c63 price_of(db: sqlite3.Connection, product_id: int=4) -> int=260  app.py:40  48us  io 1  thread 2
   r1:c67 price_of(db: sqlite3.Connection, product_id: int=3) -> int=990  app.py:40  47us  io 1  thread 2
   r1:c71 price_of(db: sqlite3.Connection, product_id: int=4) -> int=260  app.py:40  48us  io 1  thread 2
   r1:c72 price_of(db: sqlite3.Connection, product_id: int=1) -> int=450  app.py:40  50us  io 1  thread 2
   next: ormaos tree r1:c16 | ormaos tree r1:c17 | ormaos tree r1 | ormaos exceptions r1
   ['kind', 'version', 'recording', 'address', 'root', 'ancestors', 'filter', 'looked_at', 'matched', 'by_fn', 'raised', 'depth', 'limit', 'offset', 'nodes', 'not_shown', 'matches_not_shown', 'program_data', 'next', 'next_commands']
   ```
5. ```text
   .venv/bin/ormaos tree r1 --function price_of --json | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['matched'],d['looked_at'],len(d['nodes']))"
   ```

   Output, the 1 line of 1 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-values-1.jsonl?plain=1#L20)):

   ```text
   24 72 24
   ```
6. ```text
   Write answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `"Clara"` |
| q2 | right | `"0, yes"` |
| q3 | right | `8` |
| q4 | right | `18200` |
| q5 | right | `"8, 3660"` |
| q6 | right | `24` |
| q7 | right | `38` |
| q8 | right | `38` |

## What Ormaos data answered

Read from the streams: in each run of an Ormaos arm, the `ormaos` verbs in its commands up to its last write of `answers.json`. A question counts for a verb when a run that ran the verb answered it (not null); a run that ran several verbs counts under each of them.

| Question | `ormaos`: verbs (runs) | answered | right | `ormaos-values`: verbs (runs) | answered | right |
|---|---|---|---|---|---|---|
| q1 | show 3, tree 3, io 3, guide 3, exceptions 1, list 1 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 2 | 3/3 | 3/3 |
| q2 | show 3, tree 3, io 3, guide 3, exceptions 1, list 1 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 2 | 3/3 | 3/3 |
| q3 | show 3, tree 3, io 3, guide 3, exceptions 1, list 1 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 2 | 3/3 | 3/3 |
| q4 | show 3, tree 3, io 3, guide 3, exceptions 1, list 1 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 2 | 3/3 | 3/3 |
| q5 | show 3, tree 3, io 3, guide 3, exceptions 1, list 1 | 3/3 | 2/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 2 | 3/3 | 3/3 |
| q6 | show 3, tree 3, io 3, guide 3, exceptions 1, list 1 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 2 | 3/3 | 3/3 |
| q7 | show 3, tree 3, io 3, guide 3, exceptions 1, list 1 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 2 | 3/3 | 3/3 |
| q8 | show 3, tree 3, io 3, guide 3, exceptions 1, list 1 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 2 | 3/3 | 3/3 |

## Every run

Every run of every arm.

| Arm | Run | Score | Right | Null | Wrong | `ormaos` verbs before answers.json | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` | 1 | 1.00 | 8 | 0 | 0 | – | 4 | 49,569 | 25 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-none-1.jsonl) |
| `none` | 2 | 1.00 | 8 | 0 | 0 | – | 6 | 80,197 | 32 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-none-2.jsonl) |
| `none` | 3 | 1.00 | 8 | 0 | 0 | – | 6 | 82,828 | 31 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-none-3.jsonl) |
| `raw` | 1 | 1.00 | 8 | 0 | 0 | – | 5 | 72,462 | 36 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-raw-1.jsonl) |
| `raw` | 2 | 1.00 | 8 | 0 | 0 | – | 5 | 91,945 | 44 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-raw-2.jsonl) |
| `raw` | 3 | 1.00 | 8 | 0 | 0 | – | 5 | 90,646 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-raw-3.jsonl) |
| `ormaos` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, io, tree, exceptions | 5 | 94,507 | 28 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-1.jsonl) |
| `ormaos` | 2 | 1.00 | 8 | 0 | 0 | guide, show, io, tree | 5 | 85,062 | 31 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-2.jsonl) |
| `ormaos` | 3 | 0.88 | 7 | 0 | 1 | guide, show, io, tree | 5 | 101,044 | 31 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-3.jsonl) |
| `ormaos-values` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, tree, io, exceptions, logs | 6 | 120,101 | 32 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-values-1.jsonl) |
| `ormaos-values` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, tree, io, exceptions | 5 | 97,309 | 27 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-values-2.jsonl) |
| `ormaos-values` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, tree, io, logs | 5 | 98,270 | 29 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/web-backend-ormaos-values-3.jsonl) |

## The results files

- The benchmark: [knows2](https://ormaos.com/benchmarks/knows2/#web-backend)
- Results folder: [`agent-bench/knows2/results/20261127-165801`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801)
