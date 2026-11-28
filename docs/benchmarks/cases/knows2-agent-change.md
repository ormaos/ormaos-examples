# agent-change, in knows2

*Situation · knows2*

A change made by an agent. A small billing tool in a git repository that writes invoices and refunds, run at each of two commits: before and after a change that a coding agent made. Source: [`use-cases/agent-change`](https://github.com/ormaos/ormaos-examples/tree/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/use-cases/agent-change).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Mean score, per results folder and agent; no number here adds up two of them:

- 2026-11-28, `claude-code / claude-opus-5-5`, controlled: container, network limited to the model host: `none` 1.00, `raw` 1.00, `ormaos` 1.00, `ormaos-values` 1.00 (3 runs per arm)
- 2026-11-27, `claude-code / claude-opus-5-5`, earlier: bubblewrap, network open: `none` 1.00, `raw` 1.00, `ormaos` 1.00, `ormaos-values` 1.00 (3 runs per arm)

## What happened

From the run at the first commit (r1) to the run at the second (r2), the `total_cents` of `invoices.csv` went from 44270 to 41868 in all, and 9 orders changed total. In r2, `tiers.json` was opened 38 times, `discount_percent` returned 10 in 21 calls, and `line_price` dropped cents in an inexact division in 1 call.

The numbers are the oracle's answers to the questions below: [`oracle/agent-change.json`](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/oracle/agent-change.json).

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

### 2026-11-28, `claude-code / claude-opus-5-5`, controlled: container, network limited to the model host

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-none-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 4 tool calls, 53,851 tokens, 26 s

Commands, in order (4):

1. ```text
   cd /srv/agent-change; ls -la; cat questions.json; git log --stat; cat run.py
   ```
2. ```text
   cd /srv/agent-change; git show HEAD~1:billing.py; echo ----; cat billing.py; cat tiers.json returns.json invoices.csv refunds.csv .gitignore README.md; cat orders.json
   ```
3. ```text
   cd /srv/agent-change; git status --short --ignored; mkdir -p /tmp/a && cat > /tmp/a/c.py <<'EOF'
   import json
   D='/srv/agent-change/'
   o=json.load(open(D+'orders.json'));r=json.load(open(D+'returns.json'));t=json.load(open(D+'tiers.json'))
   P={"gold":10,"silver":5}
   c1=c2=gold=inex=0;s1=s2=diff=0;ref=[]
   def lp(it,cu,v):
       global c1,c2,gold,inex
       p=it['unit_cents']*it['quantity']
       if v==1: c1+=1; return p
       c2+=1; d=P.get(t.get(cu),0); gold+= d==10
       if p*(100-d)%100: inex+=1
   ```

   … 12 more lines of this command
4. ```text
   cd /srv/agent-change; echo '{"q1":38,"q2":38,"q3":44270,"q4":41868,"q5":9,"q6":21,"q7":1,"q8":"228,1620,1575"}' > answers.json; cat answers.json
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

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-raw-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 5 tool calls, 71,834 tokens, 32 s

Commands, in order (5):

1. ```text
   cd /srv/agent-change; ls -la; cat questions.json; git log --stat; git show HEAD
   ```
2. ```text
   cd /srv/agent-change; cat run.py README.md tiers.json returns.json invoices.csv refunds.csv .gitignore; git status --ignored; python3 -c "
   import json
   for r in ['r1','r2']:
     d=json.load(open(f'result-{r}.json'))
     ev=d['traceEvents']; print(r,len(ev), list(d.keys()))
     from collections import Counter
     print(Counter(e.get('name') for e in ev).most_common(25))
     print(ev[0])
   "
   ```
3. ```text
   cd /srv/agent-change; python3 -c "
   import json
   from collections import Counter
   for r in ['r1','r2']:
     ev=json.load(open(f'result-{r}.json'))['traceEvents']
     c=Counter(e.get('name') for e in ev)
     print(r,{k:v for k,v in c.items() if 'agent-change' in k or k in ('_io.open','builtins.open')})
     print([e for e in ev if 'line_price' in e.get('name','')][:2])
     print(json.load(open(f'result-{r}.json'))['viztracer_metadata'])
   "
   cat > /tmp/sim.py <<'E'
   import json
   ```

   … 18 more lines of this command
4. ```text
   cd /srv/agent-change; python3 -c "
   import json
   ev=[e for e in json.load(open('result-r2.json'))['traceEvents'] if e.get('ph')=='X']
   dp=[e for e in ev if e['name'].startswith('discount_percent')]
   op=[e for e in ev if e['name']=='_io.open']
   inside=[o for o in op if any(d['ts']<=o['ts']<=d['ts']+d['dur'] for d in dp)]
   print(len(inside))
   others=[o for o in op if o not in inside]
   for o in others:
     par=[e for e in ev if e['ts']<o['ts']<=e['ts']+e['dur'] and e is not o]
     print(min(par,key=lambda e:e['dur'])['name'] if par else None)
   "
   ```
5. ```text
   cd /srv/agent-change; cat > answers.json <<'E'
   {
     "q1": 38,
     "q2": 38,
     "q3": 44270,
     "q4": 41868,
     "q5": 9,
     "q6": 21,
     "q7": 1,
     "q8": "228,1620,1575"
   }
   E
   ```

   … 1 more line of this command

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

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 5 tool calls, 83,694 tokens, 29 s

Commands, in order (5):

1. ```text
   cd /srv/agent-change; .venv/bin/ormaos guide; cat questions.json; ls -la
   ```

   Output, the 1 line of 185 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-1.jsonl?plain=1#L3)):

   ```text
   drwxr-xr-x 1 root   root   4096 Nov 28 15:38 ..
   ```
2. ```text
   cd /srv/agent-change; cat .gitignore README.md billing.py run.py tiers.json returns.json invoices.csv refunds.csv; git show 4e69e80 --stat; git diff 4e69e80 4a57343; .venv/bin/ormaos list
   ```

   Output, the 6 lines of 194 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-1.jsonl?plain=1#L5)):

   ```text
   9002,cedar,228
   9002,228
   9007,1620
   9011,1575
    run.py       |  38 ++++++++++
   r2  2026-11-28 02:47:40  complete  exit 0  38.9ms  1 process, 113 calls, 0 exceptions (0 swallowed), 82 io  .venv/bin/python run.py
   ```
3. ```text
   cd /srv/agent-change; .venv/bin/ormaos show r1; .venv/bin/ormaos show r2 --full; .venv/bin/ormaos io r2 --limit 200
   ```

   Output, the first 15 of 52 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-1.jsonl?plain=1#L7)):

   ```text
   r1 exit 0 in 0.03s: 1 Python process, 75 calls, 0 exceptions (0 swallowed, 0 uncaught)
   command: .venv/bin/python run.py
   code: git commit 4e69e80822, no uncommitted changes
   io: 6 events (file 6)
   not collected: io: writes to the 2 files opened at run.py:18: opened for writing, and no `write` call by Python code was seen on a file of that name: if it was written, that was inside C code (`print(..., file=f)`, `csv.writer`)
   never recorded: values, and 20 more kinds of things (`ormaos show --full` lists them with the reason)
   next: ormaos tree r1:c1 | ormaos io r1
   r2 exit 0 in 0.04s: 1 Python process, 113 calls, 0 exceptions (0 swallowed, 0 uncaught)
   header: format provisional-0, ormaos 0.0.1, mode run, started 2026-11-28 02:47:40, platform linux, in .ormaos/r2
   working directory: /srv/agent-change
   environment: 5 variables, names only: HOME LANG PATH PWD PYTHONHASHSEED
   the command and what it started: cpu user 0.02s, cpu system 0.01s, largest memory of a process 21944 kB
   command: .venv/bin/python run.py
   code: git commit 4a57343a9f, no uncommitted changes
   process 1: pid 6, parent pid 2, no recorded parent; Python 3.14.4 at /srv/agent-change/.venv/bin/python; recorded: context, calls, exceptions, io, logs, dataframes, tensors; 113 calls, 0 exceptions, 1 thread, 0 tasks; ran 14.2ms; cpu user 0.01s; cpu system 0.01s; largest memory 21944 kB
   ```
4. ```text
   cd /srv/agent-change; python3 -I - <<'EOF'
   import json
   o=json.load(open('orders.json'));r=json.load(open('returns.json'));t=json.load(open('tiers.json'))
   P={"gold":10,"silver":5}
   n=0;inex=0;gold=0;s1=s2=0;diff=0;calls=0
   def lp(i,c,disc):
       global inex,gold,calls
       d=P.get(t.get(c),0) if disc else 0
       if disc:
           calls+=1
           if d==10: gold+=1
           if (i['unit_cents']*i['quantity']*(100-d))%100: inex+=1
   ```

   … 9 more lines of this command

   Output, the 4 lines of 25 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-1.jsonl?plain=1#L9)):

   ```text
   9002 cedar 240 228
   44270 41868 9 21 1 38 [228, 1620, 1575] 33
   r1: 38 of the 75 calls match --function line_price (38 line_price; 0 raised)
   r2: 38 of the 113 calls match --function discount_percent (38 discount_percent; 0 raised)
   ```
5. ```text
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

#### `ormaos-values`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-values-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 7 tool calls, 169,107 tokens, 38 s

Commands, in order (7):

1. ```text
   cd /srv/agent-change; cat questions.json; ls -la; .venv/bin/ormaos guide
   ```

   Output, the first 15 of 185 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-values-1.jsonl?plain=1#L3)):

   ```text
   {
     "questions": [
       {
         "id": "q1",
         "question": "In r1, how many times in total was billing.line_price called (counting calls from both invoice_total and refund_amount)?",
         "format": "A single integer, e.g. 42"
       },
       {
         "id": "q2",
         "question": "In r2, how many times was tiers.json opened during the execution?",
         "format": "A single integer, e.g. 42"
       },
       {
         "id": "q3",
         "question": "In r1, what was the sum of the total_cents values over all 12 rows written to invoices.csv?",
   ```
2. ```text
   cd /srv/agent-change; cat run.py billing.py tiers.json returns.json invoices.csv refunds.csv README.md; git show HEAD --stat; git show HEAD; .venv/bin/ormaos list; .venv/bin/ormaos show r1 --full; .venv/bin/ormaos show r2 --full
   ```

   Output, the 5 lines of 260 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-values-1.jsonl?plain=1#L5)):

   ```text
   9002,cedar,228
   9002,228
   9007,1620
   9011,1575
    1 file changed, 21 insertions(+), 4 deletions(-)
   ```
3. ```text
   cd /srv/agent-change; .venv/bin/ormaos tree r1 --function line_price --limit 200 | head -80; .venv/bin/ormaos tree r2 --function line_price --limit 200 | head -30; .venv/bin/ormaos tree r2 --function discount_percent --limit 5
   ```

   Output, the 4 lines of 78 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-values-1.jsonl?plain=1#L8)):

   ```text
   r1: 38 of the 75 calls match --function line_price (38 line_price; 0 raised)
   r2: 38 of the 113 calls match --function line_price (38 line_price; 0 raised)
   r2:c14 line_price(item: dict[3]="{\"sku\": \"PEN-01\", \"unit_cents\": 120, \"quantity\": 2}", ...) -> int=228  billing.py:16  103us  io 2  calls below: 1
   r2: 38 of the 113 calls match --function discount_percent (38 discount_percent; 0 raised)
   ```
4. ```text
   cd /srv/agent-change; for r in r1 r2; do for f in invoice_total refund_amount; do echo "== $r $f"; .venv/bin/ormaos tree $r --function $f --limit 100 | grep -o '^[^ ]* \|-> int=[0-9]*'; done; done; .venv/bin/ormaos tree r2 --function line_price --limit 100 | tail -12; .venv/bin/ormaos tree r2 --function discount_percent --limit 100 | grep -c 'int=10 '; .venv/bin/ormaos io r2 --kind file | head -20
   ```

   Output, the 6 lines of 95 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-values-1.jsonl?plain=1#L10)):

   ```text
   -> int=228
   -> int=228
   -> int=1620
   -> int=1575
   r2:c98 line_price(item: dict[3]="{\"sku\": \"PEN-01\", \"unit_cents\": 120, \"quantity\": 2}", ...) -> int=228  billing.py:16  95us  io 2  calls below: 1
   21
   ```
5. ```text
   cd /srv/agent-change; .venv/bin/ormaos tree r2 --function line_price --limit 100 --json > /tmp/lp.json; .venv/bin/ormaos tree r2 --function discount_percent --limit 100 --json > /tmp/dp.json; python3 -c "
   import json;d=json.load(open('/tmp/lp.json'));print(list(d.keys()));c=d.get('calls') or d.get('nodes');print(json.dumps(c[0])[:1500])"
   ```

   Output, all 2 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-values-1.jsonl?plain=1#L12)):

   ```text
   ['kind', 'version', 'recording', 'address', 'root', 'ancestors', 'filter', 'looked_at', 'matched', 'by_fn', 'raised', 'depth', 'limit', 'offset', 'nodes', 'not_shown', 'matches_not_shown', 'program_data', 'next', 'next_commands']
   {"address": "r2:c8", "file": "billing.py", "line": 16, "fn": "line_price", "depth": 0, "args": {"item": {"type": "dict", "len": 3, "keys": {"str": 3}, "values": {"str": 1, "int": 2}, "value": {"sku": "STAP-03", "unit_cents": 990, "quantity": 2}}, "customer": {"type": "str", "len": 8, "value": "borealis"}}, "out": "returned", "duration_s": 0.00017, "thread": 1, "process": 1, "calls_below": 1, "ret": {"type": "int", "value": 1980}, "io": 2}
   ```
6. ```text
   cd /srv/agent-change; python3 -c "
   import json
   lp=json.load(open('/tmp/lp.json'))['nodes'];dp=json.load(open('/tmp/dp.json'))['nodes']
   print(len(lp),len(dp),sum(1 for n in dp if n['ret']['value']==10))
   # map discount by call order: discount call address = line_price+1
   dd={int(n['address'].split('c')[1]):n['ret']['value'] for n in dp}
   k=0
   for n in lp:
     a=int(n['address'].split('c')[1]);it=n['args']['item']['value'];d=dd[a+1]
     v=it['unit_cents']*it['quantity']*(100-d)
     assert v//100==n['ret']['value']
     k+= v%100!=0
   ```

   … 5 more lines of this command
7. ```text
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

### 2026-11-27, `claude-code / claude-opus-5-5`, earlier: bubblewrap, network open

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

### 2026-11-28, `claude-code / claude-opus-5-5`, controlled: container, network limited to the model host

| Question | `ormaos`: verbs (runs) | answered | right | `ormaos-values`: verbs (runs) | answered | right |
|---|---|---|---|---|---|---|
| q1 | show 3, tree 3, list 3, guide 3, io 2, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 |
| q2 | show 3, tree 3, list 3, guide 3, io 2, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 |
| q3 | show 3, tree 3, list 3, guide 3, io 2, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 |
| q4 | show 3, tree 3, list 3, guide 3, io 2, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 |
| q5 | show 3, tree 3, list 3, guide 3, io 2, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 |
| q6 | show 3, tree 3, list 3, guide 3, io 2, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 |
| q7 | show 3, tree 3, list 3, guide 3, io 2, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 |
| q8 | show 3, tree 3, list 3, guide 3, io 2, diff 2 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 |

### 2026-11-27, `claude-code / claude-opus-5-5`, earlier: bubblewrap, network open

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

Every run of every arm, one table per results folder and agent.

### 2026-11-28, `claude-code / claude-opus-5-5`, controlled: container, network limited to the model host

| Arm | Run | Score | Right | Null | Wrong | `ormaos` verbs before answers.json | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` | 1 | 1.00 | 8 | 0 | 0 | – | 4 | 53,851 | 26 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-none-1.jsonl) |
| `none` | 2 | 1.00 | 8 | 0 | 0 | – | 4 | 48,087 | 24 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-none-2.jsonl) |
| `none` | 3 | 1.00 | 8 | 0 | 0 | – | 4 | 48,023 | 27 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-none-3.jsonl) |
| `raw` | 1 | 1.00 | 8 | 0 | 0 | – | 5 | 71,834 | 32 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-raw-1.jsonl) |
| `raw` | 2 | 1.00 | 8 | 0 | 0 | – | 4 | 53,203 | 28 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-raw-2.jsonl) |
| `raw` | 3 | 1.00 | 8 | 0 | 0 | – | 4 | 56,680 | 34 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-raw-3.jsonl) |
| `ormaos` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, io, tree | 5 | 83,694 | 29 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-1.jsonl) |
| `ormaos` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, io, diff, tree | 5 | 80,826 | 33 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-2.jsonl) |
| `ormaos` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, diff, tree | 5 | 97,469 | 34 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-3.jsonl) |
| `ormaos-values` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, tree, io | 7 | 169,107 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-values-1.jsonl) |
| `ormaos-values` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, tree | 6 | 121,009 | 42 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-values-2.jsonl) |
| `ormaos-values` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, tree, io | 7 | 176,090 | 51 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/agent-change-ormaos-values-3.jsonl) |

### 2026-11-27, `claude-code / claude-opus-5-5`, earlier: bubblewrap, network open

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
- Results folder: [`agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641`](https://github.com/ormaos/ormaos-examples/tree/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641): 2026-11-28, `claude-code / claude-opus-5-5`, controlled: container, network limited to the model host
- Results folder: [`agent-bench/knows2/results/20261127-165801`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801): 2026-11-27, `claude-code / claude-opus-5-5`, earlier: bubblewrap, network open
