# agent-change, in knows2

*Situation · knows2*

A change made by an agent. A small billing tool in a git repository that writes invoices and refunds, run at each of two commits: before and after a change that a coding agent made. Source: [`use-cases/agent-change`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/agent-change).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Mean score over every run: `none` 1.00, `raw` 1.00, `ormaos` 1.00, `ormaos-values` 1.00 (3 runs per arm). Agent: `claude-code / claude-opus-5-5`.

## What happened

From the run at the first commit (r1) to the run at the second (r2), the `total_cents` of `invoices.csv` went from 44270 to 41868 in all, and 9 orders changed total. In r2, `tiers.json` was opened 38 times, `discount_percent` returned 10 in 21 calls, and `line_price` dropped cents in an inexact division in 1 call.

The numbers are the oracle's answers to the questions below: [`oracle/agent-change.json`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/oracle/agent-change.json).

## What the agent was given

The folder the execution left, with what the arm adds, and 8 questions in `questions.json`, written by a model that was not told about Ormaos. The oracle's answers were not in the folder.

| Question | Asked | Format | The oracle's answer |
|---|---|---|---|
| q1 | In r1, how many times in total was billing.line_price called (counting calls from both invoice_total and refund_amount)? | A single integer, e.g. 42 | `38` |
| q2 | In r2, how many times was tiers.json opened during the execution? | A single integer, e.g. 42 | `38` |
| q3 | In r1, what was the sum of the total_cents values over all 12 rows written to invoices.csv? | A single integer number of cents, e.g. 123456 | `44270` |
| q4 | In r2, what was the sum of the total_cents values over all 12 rows written to invoices.csv? | A single integer number of cents, e.g. 123456 | `41868` |
| q5 | Of the 12 orders, how many had a different total_cents in r2's invoices.csv than in r1's invoices.csv? | A single integer from 0 to 12 | `9` |
| q6 | In r2, how many of the calls to billing.discount_percent returned 10 (i.e. the customer was looked up as a gold tier)? | A single integer, e.g. 7 | `21` |
| q7 | In r2, in how many calls to billing.line_price was the integer division by 100 inexact, i.e. unit_cents * quantity * (100 - discount) was not a multiple of 100, so cents were truncated? | A single integer, e.g. 3 | `1` |
| q8 | What were the three refund_cents values written to refunds.csv in r2, in the order the rows were written? | Three integers separated by commas, in row order, e.g. 1200,450,9900 | `[228, 1620, 1575]` |

**The prompt of each arm, verbatim**

`none`:

```text
This folder is a git repository with two commits. `python3 run.py` ran once at the first commit (that execution is r1) and once at the second (r2). The folder is as that left it. questions.json has questions about what happened in those executions. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
This folder is a git repository with two commits. `python3 run.py` ran once at the first commit (that execution is r1) and once at the second (r2). The folder is as that left it. questions.json has questions about what happened in those executions. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of each execution is in result-r1.json and result-r2.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
This folder is a git repository with two commits. `python3 run.py` ran once at the first commit (that execution is r1) and once at the second (r2). The folder is as that left it. questions.json has questions about what happened in those executions. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. Those executions were recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
This folder is a git repository with two commits. `python3 run.py` ran once at the first commit (that execution is r1) and once at the second (r2). The folder is as that left it. questions.json has questions about what happened in those executions. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. Those executions were recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the lines of its output that hold a value the agent wrote in `answers.json`, or its first 15 lines, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-none-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 4 tool calls, 52,881 tokens, 26 s

Commands, in order (4):

1. ```text
   cd /srv/agent-change; ls -la; cat questions.json; git log --stat; git show HEAD
   ```
2. ```text
   cd /srv/agent-change; cat run.py README.md tiers.json returns.json invoices.csv refunds.csv .gitignore; cat orders.json | head -50
   ```
3. ```text
   cd /srv/agent-change; git status --short; git diff 8e90a5e HEAD --stat -- orders.json tiers.json returns.json run.py; mkdir -p /tmp/w && cat > /tmp/w/a.py <<'EOF'
   import json
   O=json.load(open('/srv/agent-change/orders.json'));R=json.load(open('/srv/agent-change/returns.json'));T=json.load(open('/srv/agent-change/tiers.json'))
   P={"gold":10,"silver":5}
   by={o['id']:o for o in O}
   def run(v2):
     st=dict(calls=0,gold=0,inexact=0)
     def lp(it,c):
       st['calls']+=1
       p=it['unit_cents']*it['quantity']
       if not v2: return p
       d=P.get(T.get(c),0)
   ```

   … 11 more lines of this command
4. ```text
   cd /srv/agent-change; cat > answers.json <<'EOF'
   {"q1": 38, "q2": 38, "q3": 44270, "q4": 41868, "q5": 9, "q6": 21, "q7": 1, "q8": "228,1620,1575"}
   EOF
   cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `38` |
| q2 | right | `38` |
| q3 | right | `44270` |
| q4 | right | `41868` |
| q5 | right | `9` |
| q6 | right | `21` |
| q7 | right | `1` |
| q8 | right | `"228,1620,1575"` |

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-raw-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 4 tool calls, 57,203 tokens, 30 s

Commands, in order (4):

1. ```text
   cd /srv/agent-change; ls -la; cat questions.json; git log --stat; git show HEAD
   ```
2. ```text
   cd /srv/agent-change; cat run.py .gitignore tiers.json returns.json invoices.csv refunds.csv; python3 -c "
   import json
   for r in ['r1','r2']:
       d=json.load(open(f'result-{r}.json'))
       ev=d['traceEvents']
       from collections import Counter
       c=Counter(e.get('name') for e in ev if e.get('ph')=='X')
       print(r,[(k,v) for k,v in c.items() if 'billing' in k or 'open' in k or 'run.py' in k])
       print(ev[0].keys(), [e for e in ev if 'args' in e][:2])
   "
   ```
3. ```text
   cd /srv/agent-change; python3 -c "
   import json
   for r in ['r1','r2']:
       ev=json.load(open(f'result-{r}.json'))['traceEvents']
       x=[e for e in ev if e.get('ph')=='X' and ('discount' in e['name'] or '_io.open'==e['name'])]
       print(r,len(x), x[:3])
       print(set(e['ph'] for e in ev), [e for e in ev if e.get('args') and e['ph']!='M'][:3])
   "
   python3 - <<'E'
   import json
   orders=json.load(open('orders.json'));tiers=json.load(open('tiers.json'));rets=json.load(open('returns.json'))
   P={"gold":10,"silver":5}
   ```

   … 23 more lines of this command
4. ```text
   cd /srv/agent-change; cat > answers.json <<'E'
   {"q1": 38, "q2": 38, "q3": 44270, "q4": 41868, "q5": 9, "q6": 21, "q7": 1, "q8": "228,1620,1575"}
   E
   cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `38` |
| q2 | right | `38` |
| q3 | right | `44270` |
| q4 | right | `41868` |
| q5 | right | `9` |
| q6 | right | `21` |
| q7 | right | `1` |
| q8 | right | `"228,1620,1575"` |

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 5 tool calls, 101,359 tokens, 32 s

Commands, in order (5):

1. ```text
   .venv/bin/ormaos guide; cat questions.json; ls -la
   ```

   Output, the first 15 of 185 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-1.jsonl?plain=1#L5)):

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
   cat README.md billing.py run.py tiers.json returns.json invoices.csv refunds.csv orders.json .gitignore; git show --stat HEAD; git diff HEAD~1 HEAD; .venv/bin/ormaos list
   ```

   Output, the 5 lines of 426 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-1.jsonl?plain=1#L7)):

   ```text
   9002,cedar,228
   9002,228
   9007,1620
   9011,1575
    1 file changed, 21 insertions(+), 4 deletions(-)
   ```
3. ```text
   O=.venv/bin/ormaos; $O show r1 --full; $O show r2 --full; $O io r2; $O io r1; $O tree r1 --function line_price --limit 100 | tail -5; $O diff r1 r2; git status --short
   ```

   Output, the 3 lines of 105 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-1.jsonl?plain=1#L13)):

   ```text
     discount_percent at billing.py:10: none in r1, 38 in r2  [r2:c9]
     file open tiers.json (read)  at billing.py:11 in discount_percent: none in r1, 38 in r2  [r2:i5]
     file read tiers.json  at billing.py:12 in discount_percent: none in r1, 38 in r2  [r2:i6]
   ```
4. ```text
   python3 -I -c "
   import json
   o=json.load(open('orders.json'));t=json.load(open('tiers.json'));r=json.load(open('returns.json'))
   P={'gold':10,'silver':5}
   d=lambda c:P.get(t.get(c),0)
   by={x['id']:x for x in o}
   t1=[sum(i['unit_cents']*i['quantity'] for i in x['items']) for x in o]
   t2=[sum(i['unit_cents']*i['quantity']*(100-d(x['customer']))//100 for i in x['items']) for x in o]
   print(sum(t1),sum(t2),sum(a!=b for a,b in zip(t1,t2)),t2)
   calls=[(i,x['customer']) for x in o for i in x['items']]+[(i,by[q['order_id']]['customer']) for q in r for i in by[q['order_id']]['items'] if i['sku'] in q['skus']]
   print(len(calls),sum(d(c)==10 for i,c in calls),sum(i['unit_cents']*i['quantity']*(100-d(c))%100!=0 for i,c in calls))
   print([sum(i['unit_cents']*i['quantity']*(100-d(by[q['order_id']]['customer']))//100 for i in by[q['order_id']]['items'] if i['sku'] in q['skus']) for q in r])
   ```

   … 1 more line of this command
5. ```text
   cat > answers.json <<'EOF'
   {"q1": 38, "q2": 38, "q3": 44270, "q4": 41868, "q5": 9, "q6": 21, "q7": 1, "q8": "228,1620,1575"}
   EOF
   python3 -I -m json.tool answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `38` |
| q2 | right | `38` |
| q3 | right | `44270` |
| q4 | right | `41868` |
| q5 | right | `9` |
| q6 | right | `21` |
| q7 | right | `1` |
| q8 | right | `"228,1620,1575"` |

#### `ormaos-values`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-values-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 7 tool calls, 136,381 tokens, 38 s

Commands, in order (7):

1. ```text
   cd /srv/agent-change; .venv/bin/ormaos guide; cat questions.json; ls -la
   ```

   Output, the first 15 of 185 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-values-1.jsonl?plain=1#L5)):

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
   cd /srv/agent-change; cat billing.py run.py tiers.json invoices.csv refunds.csv returns.json README.md .gitignore; git show 8e90a5e:billing.py; git log --stat; .venv/bin/ormaos list; .venv/bin/ormaos show r1; .venv/bin/ormaos show r2
   ```

   Output, the 6 lines of 195 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-values-1.jsonl?plain=1#L7)):

   ```text
   9002,cedar,228
   9002,228
   9007,1620
   9011,1575
    1 file changed, 21 insertions(+), 4 deletions(-)
    run.py       |  38 ++++++++++
   ```
3. ```text
   cd /srv/agent-change; .venv/bin/ormaos tree r1 --function line_price --limit 100 | head -60; .venv/bin/ormaos tree r2 --function discount_percent --limit 100 | head -30; git status --short; git diff 8e90a5e HEAD -- tiers.json
   ```

   Output, the 2 lines of 70 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-values-1.jsonl?plain=1#L12)):

   ```text
   r1: 38 of the 75 calls match --function line_price (38 line_price; 0 raised)
   r2: 38 of the 113 calls match --function discount_percent (38 discount_percent; 0 raised)
   ```
4. ```text
   cd /srv/agent-change; for r in r1 r2; do for f in invoice_total refund_amount; do echo "$r $f"; .venv/bin/ormaos tree $r --function $f --limit 100 | grep -o '^[^ ]*\|-> int=[0-9]*'| paste - - ; done; done; .venv/bin/ormaos tree r2 --function discount_percent --limit 100 | grep -c 'int=10 '; .venv/bin/ormaos tree r2 --function line_price --limit 100 | head -3
   ```

   Output, the 6 lines of 42 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-values-1.jsonl?plain=1#L15)):

   ```text
   -> int=228	r2:c16
   -> int=228	r2:c100
   -> int=1620	r2:c106
   -> int=1575	next:
   21
   r2: 38 of the 113 calls match --function line_price (38 line_price; 0 raised)
   ```
5. ```text
   cd /srv/agent-change; .venv/bin/ormaos tree r2 --function line_price --limit 100 --json > /tmp/lp.json; python3 -I -c "
   import json
   d=json.load(open('/tmp/lp.json'))
   print(list(d.keys()))
   print(json.dumps(d,indent=0)[:1500])"
   ```

   Output, the 2 lines of 128 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-values-1.jsonl?plain=1#L21)):

   ```text
   "matched": 38,
   "line_price": 38
   ```
6. ```text
   cd /srv/agent-change; python3 -I -c "
   import json
   d=json.load(open('/tmp/lp.json'))
   disc={'borealis':0,'cedar':5,'delta':10,'acme':10}
   n=0
   for x in d['nodes']:
     it=x['args']['item']['value'];c=x['args']['customer']['value'];p=it['unit_cents']*it['quantity']*(100-disc[c])
     assert p//100==x['ret']['value']
     n+= p%100!=0
   print(n, len(d['nodes']))
   print(sum([2500,240,3020,1040,5320,4950,2910,2470,5920,7840,2350,5710]), sum([2500,228,2718,936,5320,4702,2619,2223,5920,7448,2115,5139]))
   "
   ```
7. ```text
   cd /srv/agent-change; cat > answers.json <<'EOF'
   {"q1": 38, "q2": 38, "q3": 44270, "q4": 41868, "q5": 9, "q6": 21, "q7": 1, "q8": "228,1620,1575"}
   EOF
   cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `38` |
| q2 | right | `38` |
| q3 | right | `44270` |
| q4 | right | `41868` |
| q5 | right | `9` |
| q6 | right | `21` |
| q7 | right | `1` |
| q8 | right | `"228,1620,1575"` |

## What Ormaos data answered

Read from the streams: in each run of an Ormaos arm, the `ormaos` verbs in its commands up to its last write of `answers.json`. A question counts for a verb when a run that ran the verb answered it (not null); a run that ran several verbs counts under each of them.

| Question | `ormaos`: verbs (runs) | answered | right | `ormaos-values`: verbs (runs) | answered | right |
|---|---|---|---|---|---|---|
| q1 | show 3, tree 3, io 3, list 3, guide 3, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2, diff 1 | 3/3 | 3/3 |
| q2 | show 3, tree 3, io 3, list 3, guide 3, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2, diff 1 | 3/3 | 3/3 |
| q3 | show 3, tree 3, io 3, list 3, guide 3, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2, diff 1 | 3/3 | 3/3 |
| q4 | show 3, tree 3, io 3, list 3, guide 3, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2, diff 1 | 3/3 | 3/3 |
| q5 | show 3, tree 3, io 3, list 3, guide 3, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2, diff 1 | 3/3 | 3/3 |
| q6 | show 3, tree 3, io 3, list 3, guide 3, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2, diff 1 | 3/3 | 3/3 |
| q7 | show 3, tree 3, io 3, list 3, guide 3, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2, diff 1 | 3/3 | 3/3 |
| q8 | show 3, tree 3, io 3, list 3, guide 3, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2, diff 1 | 3/3 | 3/3 |

## Every run

Every run of every arm.

| Arm | Run | Score | Right | Null | Wrong | `ormaos` verbs before answers.json | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` | 1 | 1.00 | 8 | 0 | 0 | – | 4 | 52,881 | 26 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-none-1.jsonl) |
| `none` | 2 | 1.00 | 8 | 0 | 0 | – | 4 | 57,847 | 26 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-none-2.jsonl) |
| `none` | 3 | 1.00 | 8 | 0 | 0 | – | 4 | 52,196 | 24 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-none-3.jsonl) |
| `raw` | 1 | 1.00 | 8 | 0 | 0 | – | 4 | 57,203 | 30 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-raw-1.jsonl) |
| `raw` | 2 | 1.00 | 8 | 0 | 0 | – | 5 | 75,422 | 32 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-raw-2.jsonl) |
| `raw` | 3 | 1.00 | 8 | 0 | 0 | – | 5 | 74,146 | 33 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-raw-3.jsonl) |
| `ormaos` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, io, tree, diff | 5 | 101,359 | 32 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-1.jsonl) |
| `ormaos` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, io, tree | 7 | 121,340 | 41 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-2.jsonl) |
| `ormaos` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, io, tree, diff | 5 | 89,349 | 31 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-3.jsonl) |
| `ormaos-values` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, tree | 7 | 136,381 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-values-1.jsonl) |
| `ormaos-values` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, tree, io | 8 | 164,324 | 45 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-values-2.jsonl) |
| `ormaos-values` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, io, tree, diff | 7 | 137,166 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/agent-change-ormaos-values-3.jsonl) |

## The results files

- The benchmark: [knows2](https://ormaos.com/benchmarks/knows2/#agent-change)
- Results folder: [`agent-bench/knows2/results/20261127-165801`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801), earlier: bubblewrap, network open
