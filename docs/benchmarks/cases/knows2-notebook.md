# notebook, in knows2

*Situation · knows2*

A notebook. A Jupyter notebook that reads the sales of the week, leaves out single sales above a limit, adds tax and sums the week; its cells ran in the order of their saved execution counts. Source: [`use-cases/notebook`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/notebook).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Mean score over every run: `none` 0.50, `raw` 0.62, `ormaos` 0.62, `ormaos-values` 0.62 (3 runs per arm). Agent: `claude-code / claude-opus-5-5`.

## What happened

`load("sales.csv")` returned 40 rows, and the third cell the kernel ran was `cell-4`. `drop_key_accounts` compared prices that were tax-inclusive and left 22 rows; 12 of the rows it took out had a price within the limit before tax. At the end `week` held 15602.40, over rows with 42 items in all.

The numbers are the oracle's answers to the questions below: [`oracle/notebook.json`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/oracle/notebook.json).

## What the agent was given

The folder the execution left, with what the arm adds, and 8 questions in `questions.json`, written by a model that was not told about Ormaos. The oracle's answers were not in the folder.

| Question | Asked | Format | The oracle's answer |
|---|---|---|---|
| q1 | How many rows did load("sales.csv") return in this execution, i.e. what was len(rows) right after the cell with id cell-2 ran? | integer, e.g. 37 | `40` |
| q2 | Following the saved execution counts, which code cell (by cell id) was the third one executed in the kernel? | a cell id string, e.g. cell-3 | `"cell-4"` |
| q3 | When drop_key_accounts compared each row's price to LIMIT in this execution, was that price the original price from sales.csv or the price with 20% tax already added? | one of: pre-tax, tax-inclusive | `"tax-inclusive"` |
| q4 | How many rows were left in rows after drop_key_accounts(rows) returned in this execution? | integer, e.g. 31 | `22` |
| q5 | How many rows had an original price of at most 1000 in sales.csv but were still removed by drop_key_accounts in this execution, because their price had been increased by the tax before the filter ran? | integer, e.g. 4 | `12` |
| q6 | What value did the variable week hold at the end of the execution, rounded to two decimal places? | decimal number with exactly two decimals, e.g. 12345.67 | `15602.4` |
| q7 | What was the highest price among the rows that remained in rows at the end of the execution (the tax-inclusive price used in the final total)? | decimal number with exactly two decimals, e.g. 999.60 | `936.0` |
| q8 | What was the sum of the quantity field over all rows that remained in rows at the end of the execution? | integer, e.g. 120 | `42` |

**The prompt of each arm, verbatim**

`none`:

```text
The code cells of report.ipynb ran once in a Jupyter kernel of `.venv/bin/python`, in this folder, in the order of the execution counts saved in the notebook. The folder is as that left it, without the input it read (sales.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
The code cells of report.ipynb ran once in a Jupyter kernel of `.venv/bin/python`, in this folder, in the order of the execution counts saved in the notebook. The folder is as that left it, without the input it read (sales.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
The code cells of report.ipynb ran once in a Jupyter kernel of `.venv/bin/python`, in this folder, in the order of the execution counts saved in the notebook. The folder is as that left it, without the input it read (sales.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
The code cells of report.ipynb ran once in a Jupyter kernel of `.venv/bin/python`, in this folder, in the order of the execution counts saved in the notebook. The folder is as that left it, without the input it read (sales.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the lines of its output that hold a value the agent wrote in `answers.json`, or its first 15 lines, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-none-1.jsonl)
- Score 0.50: 4 right, 4 null, 0 wrong
- 4 tool calls, 50,736 tokens, 24 s

Commands, in order (4):

1. ```text
   cd /srv/notebook; ls -la; cat questions.json; python3 -c "
   import json;nb=json.load(open('report.ipynb'))
   for c in nb['cells']:
     print('----',c['cell_type'],c.get('execution_count'));print(''.join(c['source']))
     for o in c.get('outputs',[]): print('OUT:',json.dumps(o)[:1500])
   "
   ```
2. ```text
   cd /srv/notebook; cat README.md run_notebook.py requirements.txt; grep -o '"id": "[^"]*"' report.ipynb; ls -la .venv; find / -name "*ormaos*" -not -path /proc 2>/dev/null | head
   ```
3. ```text
   cd /srv/notebook; python3 -c "
   import json;nb=json.load(open('report.ipynb'))
   for c in nb['cells']: print(c['id'],c.get('execution_count'),c['source'][:2] if c['cell_type']=='code' else '')"; cat .venv/lib/python3.14/site-packages/ormaos.py; ls -la ~ /tmp; find / -newer report.ipynb -type f -not -path '/proc/*' -not -path '/sys/*' 2>/dev/null | grep -v '^/dev' | head -30
   ```
4. ```text
   cd /srv/notebook; cat > answers.json <<'E'
   {"q1": 40, "q2": "cell-4", "q3": "tax-inclusive", "q4": null, "q5": null, "q6": "15602.40", "q7": null, "q8": null}
   E
   cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `40` |
| q2 | right | `"cell-4"` |
| q3 | right | `"tax-inclusive"` |
| q4 | null |  |
| q5 | null |  |
| q6 | right | `"15602.40"` |
| q7 | null |  |
| q8 | null |  |

Its own words on q4, q5, q7 and q8: the paragraphs of its last message that name them

```text
| id | answer | evidence |
|---|---|---|
| q1 | `40` | The saved output of cell-2 is `40`. |
| q2 | `"cell-4"` | The execution counts are cell-1=1, cell-2=2, **cell-4=3**, cell-3=4, cell-5=5. So `add_tax` (cell-4) ran before `drop_key_accounts` (cell-3). |
| q3 | `"tax-inclusive"` | Because of that order, the filter compared prices that already included the 20% tax against `LIMIT`. |
| q4 | `null` | |
| q5 | `null` | |
| q6 | `"15602.40"` | The saved output of cell-5 is `week total with tax: 15602.40`. |
| q7 | `null` | |
| q8 | `null` | |

**Why q4, q5, q7 and q8 are null:** each one depends on individual rows. The notebook only kept the row count and the final total. The `ormaos` package in `.venv` is a stand-in whose `record()` does nothing, so no recording of the steps exists either. I found no other leftover files from the run.
```

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-raw-1.jsonl)
- Score 0.62: 5 right, 3 null, 0 wrong
- 5 tool calls, 79,759 tokens, 38 s

Commands, in order (5):

1. ```text
   cd /srv/notebook; ls -la; cat questions.json; python3 -c "
   import json;nb=json.load(open('report.ipynb'))
   for c in nb['cells']:
     print('---',c['cell_type'],c.get('execution_count'));print(''.join(c['source']))
     for o in c.get('outputs',[]): print('OUT:',json.dumps(o)[:1500])
   "
   ```
2. ```text
   cd /srv/notebook; python3 -c "
   import json;nb=json.load(open('report.ipynb'))
   print([(c.get('id'),c.get('execution_count')) for c in nb['cells']])"; cat README.md run_notebook.py requirements.txt; ls .venv/lib/*/site-packages | head -50; head -c 1500 result.json
   ```
3. ```text
   cd /srv/notebook; cat .venv/lib/*/site-packages/ormaos.py | head -150; python3 -c "
   import json,collections
   d=json.load(open('result.json'))
   ev=d['traceEvents']
   print(len(ev), d.keys())
   c=collections.Counter(e.get('name') for e in ev if 'ormaos' in str(e.get('name')) or '<module>' in str(e.get('name')) or 'load' in str(e.get('name')) or 'drop' in str(e.get('name')) or 'add_tax' in str(e.get('name')) or 'total' in str(e.get('name')) or 'listcomp' in str(e.get('name')) or 'genexpr' in str(e.get('name')))
   for k,v in c.most_common(60): print(v,k)
   print([e for e in ev if 'args' in e and e.get('ph')!='M'][:5])
   "
   ```
4. ```text
   cd /srv/notebook; python3 -c "
   import json,collections
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X']
   tg=[e for e in ev if '/tmp/' in e['name'] or 'ipykernel_' in e['name']]
   c=collections.Counter(e['name'] for e in tg)
   for k,v in c.items(): print(v,k)
   for n in ['load','drop_key_accounts','add_tax','total']:
     for e in ev:
       if e['name'].startswith(n+' ('): 
         t0,t1=e['ts'],e['ts']+e['dur']
         inner=collections.Counter(x['name'] for x in ev if t0<=x['ts']<=t1 and x['tid']==e['tid'])
   ```

   … 2 more lines of this command
5. ```text
   cd /srv/notebook; cat > answers.json <<'E'
   {"q1": 40, "q2": "cell-4", "q3": "tax-inclusive", "q4": 22, "q5": null, "q6": "15602.40", "q7": null, "q8": null}
   E
   python3 -m json.tool answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `40` |
| q2 | right | `"cell-4"` |
| q3 | right | `"tax-inclusive"` |
| q4 | right | `22` |
| q5 | null |  |
| q6 | right | `"15602.40"` |
| q7 | null |  |
| q8 | null |  |

Its own words on q5, q7 and q8: the paragraphs of its last message that name them

```text
| id | answer | where it comes from |
|---|---|---|
| q1 | 40 | The saved output of cell-2. The trace agrees: `DictReader.__next__` was called 41 times (40 rows plus the end of file). |
| q2 | cell-4 | Execution counts by cell: cell-1=1, cell-2=2, **cell-4=3**, cell-3=4, cell-5=5. |
| q3 | tax-inclusive | The cells ran out of their order on the page: `add_tax` (cell-4) ran before `drop_key_accounts` (cell-3). The trace timestamps confirm this (`add_tax` at …779400, `drop_key_accounts` at …784154). So the filter saw prices with the 20% tax already added. |
| q4 | 22 | `total`'s generator was entered 23 times, which means 22 rows (one extra entry at the end). |
| q6 | "15602.40" | The printed output of cell-5. |
| q5, q7, q8 | null | `sales.csv` isn't here, and the trace doesn't record argument or return values. So I can't recover individual prices or quantities. |
```

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-1.jsonl)
- Score 0.62: 5 right, 3 null, 0 wrong
- 5 tool calls, 83,364 tokens, 28 s

Commands, in order (5):

1. ```text
   cd /srv/notebook; ls -la; cat questions.json; .venv/bin/ormaos guide
   ```

   Output, the first 15 of 179 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-1.jsonl?plain=1#L5)):

   ```text
   total 32
   drwxrwxr-x 4 levimbraga levimbraga 4096 Nov 27 16:57 .
   drwx------ 3 levimbraga levimbraga   60 Nov 27 16:59 ..
   drwxrwxr-x 6 levimbraga levimbraga 4096 Nov 27 16:57 .ormaos
   drwxrwxr-x 6 levimbraga levimbraga 4096 Nov 27 13:56 .venv
   -rw-rw-r-- 1 levimbraga levimbraga  855 Nov 27 13:26 README.md
   -rw-rw-r-- 1 levimbraga levimbraga 1864 Nov 27 16:57 questions.json
   -rw-rw-r-- 1 levimbraga levimbraga 2645 Nov 27 13:25 report.ipynb
   -rw-rw-r-- 1 levimbraga levimbraga   46 Nov 27 13:25 requirements.txt
   -rw-rw-r-- 1 levimbraga levimbraga  686 Nov 27 13:25 run_notebook.py
   {
     "questions": [
       {
         "id": "q1",
         "question": "How many rows did load(\"sales.csv\") return in this execution, i.e. what was len(rows) right after the cell with id cell-2 ran?",
   ```
2. ```text
   cd /srv/notebook; cat README.md run_notebook.py; python3 -c "
   import json;nb=json.load(open('report.ipynb'))
   for c in nb['cells']: print(c.get('id'),c['cell_type'],c.get('execution_count'));print(''.join(c['source']));print(c.get('outputs'));print('---')"; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the 2 lines of 141 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-1.jsonl?plain=1#L7)):

   ```text
   [{'data': {'text/plain': ['40']}, 'execution_count': 2, 'metadata': {}, 'output_type': 'execute_result'}]
   cell-4 code 3
   ```
3. ```text
   cd /srv/notebook; for r in r1 r2 r3 r4; do .venv/bin/ormaos tree $r; .venv/bin/ormaos exceptions $r; done; .venv/bin/ormaos io r1
   ```

   Output, the 4 lines of 21 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-1.jsonl?plain=1#L12)):

   ```text
   r1:c1 load(path: str[9]) -> list[40 dict]  /tmp/ipykernel_3/1887773198.py:9  246us  io 1  task 1
   r2:c1 add_tax(rows: list[40 dict]) -> list[40 dict]  /tmp/ipykernel_3/1887773198.py:21  100us  task 1
   r3:c1 drop_key_accounts(rows: list[40 dict]) -> list[22 dict]  /tmp/ipykernel_3/1887773198.py:17  50us  task 1
   r4:c1 total(rows: list[22 dict]) -> float  /tmp/ipykernel_3/1887773198.py:25  205us  task 1  calls below: 1
   ```
4. ```text
   cd /srv/notebook; cat > answers.json <<'E'
   {"q1": 40, "q2": "cell-4", "q3": "tax-inclusive", "q4": 22, "q5": null, "q6": "15602.40", "q7": null, "q8": null}
   E
   python3 -m json.tool answers.json
   ```
5. ```text
   cd /srv/notebook; sed -i 's/"15602.40"/15602.40/' answers.json; cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `40` |
| q2 | right | `"cell-4"` |
| q3 | right | `"tax-inclusive"` |
| q4 | right | `22` |
| q5 | null |  |
| q6 | right | `15602.4` |
| q7 | null |  |
| q8 | null |  |

Its own words on q5, q7 and q8: the paragraphs of its last message that name them

````text
```json
{"q1": 40, "q2": "cell-4", "q3": "tax-inclusive", "q4": 22, "q5": null, "q6": 15602.40, "q7": null, "q8": null}
```

- **q1 = 40:** `load` returned a list of 40 dicts (recording r1), and cell-2's saved output is `40`.
- **q2 = cell-4:** it has execution count 3.
- **q3 = tax-inclusive:** `add_tax` (r2) ran before `drop_key_accounts` (r3), so the limit of 1000 was checked against prices that already included the 20% tax.
- **q4 = 22:** `drop_key_accounts` went from a list of 40 dicts to 22 (r3), and `total` then got those 22 (r4).
- **q6 = 15602.40:** this is cell-5's printed output, `week total with tax: 15602.40`. The README's 47498.40 is from a top-to-bottom run, not this one.
- **q5, q7, q8 = null:** these need actual prices and quantities. The recording keeps only types and lengths, and the input file isn't there anymore.
````

#### `ormaos-values`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-values-1.jsonl)
- Score 0.62: 5 right, 3 null, 0 wrong
- 6 tool calls, 120,463 tokens, 34 s

Commands, in order (6):

1. ```text
   ls -la && cat questions.json && .venv/bin/ormaos guide
   ```

   Output, the first 15 of 179 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-values-1.jsonl?plain=1#L5)):

   ```text
   total 32
   drwxrwxr-x 4 levimbraga levimbraga 4096 Nov 27 16:57 .
   drwx------ 3 levimbraga levimbraga   60 Nov 27 16:59 ..
   drwxrwxr-x 6 levimbraga levimbraga 4096 Nov 27 16:57 .ormaos
   drwxrwxr-x 6 levimbraga levimbraga 4096 Nov 27 13:56 .venv
   -rw-rw-r-- 1 levimbraga levimbraga  855 Nov 27 13:26 README.md
   -rw-rw-r-- 1 levimbraga levimbraga 1864 Nov 27 16:57 questions.json
   -rw-rw-r-- 1 levimbraga levimbraga 2645 Nov 27 13:25 report.ipynb
   -rw-rw-r-- 1 levimbraga levimbraga   46 Nov 27 13:25 requirements.txt
   -rw-rw-r-- 1 levimbraga levimbraga  686 Nov 27 13:25 run_notebook.py
   {
     "questions": [
       {
         "id": "q1",
         "question": "How many rows did load(\"sales.csv\") return in this execution, i.e. what was len(rows) right after the cell with id cell-2 ran?",
   ```
2. ```text
   cat README.md run_notebook.py; python3 -c "
   import json;nb=json.load(open('report.ipynb'))
   for c in nb['cells']: print(c.get('id'),c['cell_type'],c.get('execution_count'));print(''.join(c['source']));print('OUT',c.get('outputs'));print('---')"; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the 3 lines of 142 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-values-1.jsonl?plain=1#L7)):

   ```text
   OUT [{'data': {'text/plain': ['40']}, 'execution_count': 2, 'metadata': {}, 'output_type': 'execute_result'}]
   cell-4 code 3
   OUT [{'name': 'stdout', 'output_type': 'stream', 'text': ['week total with tax: 15602.40\n']}]
   ```
3. ```text
   for r in r1 r2 r3 r4; do .venv/bin/ormaos tree $r --json; echo; done | head -c 60000
   ```

   Output, the first 15 of the 18 lines of 595 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-values-1.jsonl?plain=1#L12)):

   ```text
           "len": 40,
             "dict": 40
             "...[40 items]"
             "len": 40,
               "dict": 40
               "...[40 items]"
           "len": 40,
             "dict": 40
             "...[40 items]"
             "len": 40,
               "dict": 40
               "...[40 items]"
           "len": 22,
             "dict": 22
             "...[22 items]"
   ```
4. ```text
   find .ormaos -type f | xargs ls -la; .venv/bin/ormaos exceptions r1
   ```

   Output, all 12 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-values-1.jsonl?plain=1#L17)):

   ```text
   -rw-rw-r-- 1 levimbraga levimbraga   37 Nov 27 16:57 .ormaos/.gitignore
   -rw------- 1 levimbraga levimbraga 9253 Nov 27 16:57 .ormaos/r1/p3-1795809426584663600.jsonl
   -rw-rw-r-- 1 levimbraga levimbraga 1127 Nov 27 16:57 .ormaos/r1/run.jsonl
   -rw------- 1 levimbraga levimbraga 9366 Nov 27 16:57 .ormaos/r2/p3-1795809426602911477.jsonl
   -rw-rw-r-- 1 levimbraga levimbraga 1108 Nov 27 16:57 .ormaos/r2/run.jsonl
   -rw------- 1 levimbraga levimbraga 9385 Nov 27 16:57 .ormaos/r3/p3-1795809426608423890.jsonl
   -rw-rw-r-- 1 levimbraga levimbraga 1108 Nov 27 16:57 .ormaos/r3/run.jsonl
   -rw------- 1 levimbraga levimbraga 9139 Nov 27 16:57 .ormaos/r4/p3-1795809426614806743.jsonl
   -rw-rw-r-- 1 levimbraga levimbraga 1108 Nov 27 16:57 .ormaos/r4/run.jsonl
   r1: 1 exception (0 swallowed, 0 uncaught, 1 StopIteration taken by the interpreter)
   1x StopIteration taken by the interpreter, at /usr/lib/python3.14/csv.py:177 in DictReader.__next__  [r1:e1]
   next: (nothing)
   ```
5. ```text
   grep -o '"\.\.\.[^"]*"' .ormaos/*/p3*.jsonl | sort | uniq -c; grep -c '' .ormaos/r3/p3*.jsonl; grep -o '"price": *[0-9.]*' .ormaos/r3/p3*.jsonl | wc -l
   ```
6. ```text
   Write answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `40` |
| q2 | right | `"cell-4"` |
| q3 | right | `"tax-inclusive"` |
| q4 | right | `22` |
| q5 | null |  |
| q6 | right | `"15602.40"` |
| q7 | null |  |
| q8 | null |  |

Its own words on q5, q7 and q8: the paragraphs of its last message that name them

```text
| id | answer | how I know |
|---|---|---|
| q1 | 40 | The output saved in cell-2 is `40`, and in recording r1 `load` returned a list of 40 items. |
| q2 | cell-4 | The saved execution counts are cell-1=1, cell-2=2, cell-4=3, cell-3=4, cell-5=5. So `add_tax` ran before `drop_key_accounts`. |
| q3 | tax-inclusive | Because of that order, recording r3 shows `drop_key_accounts` receiving prices that already include the tax (144.0, 936.0, 2160.0…). |
| q4 | 22 | In r3 `drop_key_accounts` returned 22 rows, and in r4 `total` received 22. |
| q5 | null | See below. |
| q6 | "15602.40" | `total` returned 15602.4, and the cell printed `week total with tax: 15602.40`. |
| q7 | null | See below. |
| q8 | null | See below. |
```

## What Ormaos data answered

Read from the streams: in each run of an Ormaos arm, the `ormaos` verbs in its commands up to its last write of `answers.json`. A question counts for a verb when a run that ran the verb answered it (not null); a run that ran several verbs counts under each of them.

| Question | `ormaos`: verbs (runs) | answered | right | `ormaos-values`: verbs (runs) | answered | right |
|---|---|---|---|---|---|---|
| q1 | show 3, tree 3, exceptions 3, list 3, guide 3, io 2 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, list 3, guide 3 | 3/3 | 3/3 |
| q2 | show 3, tree 3, exceptions 3, list 3, guide 3, io 2 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, list 3, guide 3 | 3/3 | 3/3 |
| q3 | show 3, tree 3, exceptions 3, list 3, guide 3, io 2 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, list 3, guide 3 | 3/3 | 3/3 |
| q4 | show 3, tree 3, exceptions 3, list 3, guide 3, io 2 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, list 3, guide 3 | 3/3 | 3/3 |
| q5 | – | 0/3 | 0/3 | – | 0/3 | 0/3 |
| q6 | show 3, tree 3, exceptions 3, list 3, guide 3, io 2 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, list 3, guide 3 | 3/3 | 3/3 |
| q7 | – | 0/3 | 0/3 | – | 0/3 | 0/3 |
| q8 | – | 0/3 | 0/3 | – | 0/3 | 0/3 |

## Every run

Every run of every arm.

| Arm | Run | Score | Right | Null | Wrong | `ormaos` verbs before answers.json | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` | 1 | 0.50 | 4 | 4 | 0 | – | 4 | 50,736 | 24 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-none-1.jsonl) |
| `none` | 2 | 0.50 | 4 | 4 | 0 | – | 4 | 52,053 | 23 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-none-2.jsonl) |
| `none` | 3 | 0.50 | 4 | 4 | 0 | – | 4 | 51,923 | 22 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-none-3.jsonl) |
| `raw` | 1 | 0.62 | 5 | 3 | 0 | – | 5 | 79,759 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-raw-1.jsonl) |
| `raw` | 2 | 0.62 | 5 | 3 | 0 | – | 7 | 113,451 | 53 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-raw-2.jsonl) |
| `raw` | 3 | 0.62 | 5 | 3 | 0 | – | 7 | 115,303 | 51 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-raw-3.jsonl) |
| `ormaos` | 1 | 0.62 | 5 | 3 | 0 | guide, list, show, tree, exceptions, io | 5 | 83,364 | 28 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-1.jsonl) |
| `ormaos` | 2 | 0.62 | 5 | 3 | 0 | guide, list, show, tree, exceptions, io | 5 | 85,441 | 27 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-2.jsonl) |
| `ormaos` | 3 | 0.62 | 5 | 3 | 0 | guide, list, show, tree, exceptions | 6 | 102,663 | 30 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-3.jsonl) |
| `ormaos-values` | 1 | 0.62 | 5 | 3 | 0 | guide, list, show, tree, exceptions | 6 | 120,463 | 34 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-values-1.jsonl) |
| `ormaos-values` | 2 | 0.62 | 5 | 3 | 0 | guide, list, show, tree, exceptions | 7 | 159,287 | 35 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-values-2.jsonl) |
| `ormaos-values` | 3 | 0.62 | 5 | 3 | 0 | guide, list, show, tree, exceptions | 7 | 127,594 | 35 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/notebook-ormaos-values-3.jsonl) |

## The results files

- The benchmark: [knows2](https://ormaos.com/benchmarks/knows2/#notebook)
- Results folder: [`agent-bench/knows2/results/20261127-165801`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801), earlier: bubblewrap, network open
