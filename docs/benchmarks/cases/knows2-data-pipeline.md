# data-pipeline, in knows2

*Situation · knows2*

A data pipeline. A monthly report made with pandas from two exports: it drops the orders without an amount and repeated order numbers, joins each order to its customer and sums the amounts by region. Source: [`use-cases/data-pipeline`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/data-pipeline).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Mean score over every run: `none` 0.25, `raw` 0.38, `ormaos` 0.88, `ormaos-values` 0.92 (3 runs per arm). Agent: `claude-code / claude-opus-5-5`.

## What happened

`load_orders` read 200 rows; `drop_unpriced` removed 5 without an amount, and `drop_repeats` did not run. Of the 195 rows passed to `join_customers`, 17 had a `customer_id` that is not in `customers.csv`, and the joined frame had 178 rows. The amounts of `report.csv` add up to 17182.34; its first row is `east`, 4349.29.

The numbers are the oracle's answers to the questions below: [`oracle/data-pipeline.json`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/oracle/data-pipeline.json).

## What the agent was given

The folder the execution left, with what the arm adds, and 8 questions in `questions.json`, written by a model that was not told about Ormaos. The oracle's answers were not in the folder.

| Question | Asked | Format | The oracle's answer |
|---|---|---|---|
| q1 | How many rows did the orders DataFrame have right after load_orders read orders.csv, before any filtering? | A non-negative integer, e.g. 200 | `200` |
| q2 | How many order rows did drop_unpriced remove because their amount was missing (NaN)? | A non-negative integer, e.g. 3 | `5` |
| q3 | Was drop_repeats actually called during this run, i.e. did orders['order_id'].duplicated().any() evaluate to True after the unpriced orders were dropped? | "yes" or "no" | `false` |
| q4 | How many rows did the orders DataFrame have immediately before being passed to join_customers (after drop_unpriced and, if it ran, drop_repeats)? | A non-negative integer, e.g. 195 | `195` |
| q5 | How many rows did the joined DataFrame returned by join_customers (inner merge on customer_id) have? | A non-negative integer, e.g. 190 | `178` |
| q6 | How many order rows that reached join_customers were lost in the inner merge because their customer_id had no match in customers.csv? | A non-negative integer, e.g. 0 | `17` |
| q7 | Which region appears in the first data row of report.csv (the alphabetically first region after sorting), and what is its total amount as written? | Region name and amount separated by a comma, e.g. "North, 12345.67" | `["east", 4349.29]` |
| q8 | What is the sum of the amount column over all 4 rows of the report written to report.csv? | A decimal number rounded to 2 decimal places, e.g. 48210.55 | `17182.34` |

**The prompt of each arm, verbatim**

`none`:

```text
`.venv/bin/python pipeline.py` ran once in this folder. The folder is as that left it, without the input it read (orders.csv, customers.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
`.venv/bin/python pipeline.py` ran once in this folder. The folder is as that left it, without the input it read (orders.csv, customers.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
`.venv/bin/python pipeline.py` ran once in this folder. The folder is as that left it, without the input it read (orders.csv, customers.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
`.venv/bin/python pipeline.py` ran once in this folder. The folder is as that left it, without the input it read (orders.csv, customers.csv). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the lines of its output that hold a value the agent wrote in `answers.json`, or its first 15 lines, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-none-1.jsonl)
- Score 0.25: 2 right, 6 null, 0 wrong
- 4 tool calls, 53,763 tokens, 30 s

Commands, in order (4):

1. ```text
   cd /srv/data-pipeline; ls -la; cat questions.json; cat pipeline.py
   ```
2. ```text
   cd /srv/data-pipeline; cat README.md requirements.txt; cat report.csv; ls -la .venv .venv/*; find . -newer pipeline.py -not -path './.venv/lib/*' | head -50; find / -name "orders*.csv" -o -name "customers*.csv" 2>/dev/null | head
   ```
3. ```text
   cd /srv/data-pipeline/.venv/lib/python3.14/site-packages; ls -la; ls *.pth 2>/dev/null; cat *.pth 2>/dev/null | head; ls sitecustomize* usercustomize* 2>/dev/null; find / -newer /srv/data-pipeline/pipeline.py -type f -not -path '/proc/*' -not -path '/sys/*' -not -path '*/site-packages/*' 2>/dev/null | head -40; find / -name "*.log" -mmin -300 2>/dev/null | grep -v proc | head; ls -la ~ /tmp
   ```
4. ```text
   cd /srv/data-pipeline; cat > answers.json <<'EOF'
   {
     "q1": null,
     "q2": null,
     "q3": null,
     "q4": null,
     "q5": null,
     "q6": null,
     "q7": "east, 4349.29",
     "q8": 17182.34
   }
   EOF
   ```

   … 1 more line of this command

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | null |  |
| q2 | null |  |
| q3 | null |  |
| q4 | null |  |
| q5 | null |  |
| q6 | null |  |
| q7 | right | `"east, 4349.29"` |
| q8 | right | `17182.34` |

Its own words on q1, q2, q3, q4, q5 and q6: the paragraphs of its last message that name them

```text
**`null`, q1–q6:** These need row counts from inside the run: rows loaded, rows dropped for a missing amount, whether repeated order IDs were dropped, and rows lost in the join. `orders.csv` and `customers.csv` are gone. The script logs nothing beyond its one-line summary, and I couldn't find any log, cache or leftover output on the system that records these counts.

The README says the orders export holds "200 orders of October", but I didn't use that for q1. It describes the usual export, not the file this run actually read. If that file had repeated order IDs, it would have had more than 200 rows.
```

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-raw-1.jsonl)
- Score 0.38: 3 right, 5 null, 0 wrong
- 4 tool calls, 52,598 tokens, 27 s

Commands, in order (4):

1. ```text
   cd /srv/data-pipeline; ls -la; cat questions.json; cat pipeline.py; ls -la result.json
   ```
2. ```text
   cd /srv/data-pipeline; cat report.csv; cat README.md; python3 -c "
   import json
   d=json.load(open('result.json'))
   ev=d['traceEvents']; print(len(ev), [k for k in d if k!='traceEvents'])
   import collections
   for e in ev:
     n=e.get('name','')
     if 'pipeline.py' in n or 'args' in e: print(e)
   " | head -50
   ```
3. ```text
   cd /srv/data-pipeline; python3 -c "
   import json
   d=json.load(open('result.json'))
   print(d['viztracer_metadata']); print(list(d['file_info'].keys())[:5] if isinstance(d['file_info'],dict) else 0)
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X']
   for fn in ['load_orders','drop_unpriced','join_customers']:
     m=[e for e in ev if e['name'].startswith(fn+' (')][0]
     inner=[e for e in ev if m['ts']<=e['ts']<=m['ts']+m['dur'] and e is not m]
     import collections
     c=collections.Counter(e['name'] for e in inner)
     print(fn,len(inner)); print(c.most_common(15))
   "
   ```
4. ```text
   cd /srv/data-pipeline; cat > answers.json <<'E'
   {"q1": null, "q2": null, "q3": "no", "q4": null, "q5": null, "q6": null, "q7": "east, 4349.29", "q8": 17182.34}
   E
   cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | null |  |
| q2 | null |  |
| q3 | right | `"no"` |
| q4 | null |  |
| q5 | null |  |
| q6 | null |  |
| q7 | right | `"east, 4349.29"` |
| q8 | right | `17182.34` |

Its own words on q1, q2, q4, q5 and q6: the paragraphs of its last message that name them

```text
| id | answer | source |
|---|---|---|
| q1 | null | row count after load not recorded |
| q2 | null | number of rows dropped not recorded |
| q3 | "no" | the trace has calls to `load_orders`, `load_customers`, `drop_unpriced`, `join_customers`, `revenue_by_region` and `write_report`, but none to `drop_repeats`, so the duplicate check was False |
| q4 | null | not recorded |
| q5 | null | not recorded |
| q6 | null | not recorded |
| q7 | "east, 4349.29" | first data row of `report.csv` |
| q8 | 17182.34 | 4349.29 + 2567.98 + 6196.49 + 4068.58 |

**Why the row counts are null:** the trace only has function names, start times and durations, with no arguments or return values. pandas reads, filters and merges the rows in compiled code, so no traced call repeats once per row that I could count. The README says the orders file has "200 orders", but that describes the export in general, not the file this run read. So I didn't use it for q1.
```

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-1.jsonl)
- Score 0.88: 7 right, 1 null, 0 wrong
- 3 tool calls, 51,313 tokens, 26 s

Commands, in order (3):

1. ```text
   ls -la && cat questions.json && .venv/bin/ormaos guide
   ```

   Output, the first 15 of 179 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-1.jsonl?plain=1#L4)):

   ```text
   total 32
   drwxrwxr-x 4 levimbraga levimbraga 4096 Nov 27 16:56 .
   drwx------ 3 levimbraga levimbraga   60 Nov 27 16:58 ..
   drwxrwxr-x 3 levimbraga levimbraga 4096 Nov 27 16:56 .ormaos
   drwxrwxr-x 5 levimbraga levimbraga 4096 Nov 27 13:56 .venv
   -rw-rw-r-- 1 levimbraga levimbraga  637 Nov 27 13:20 README.md
   -rw-rw-r-- 1 levimbraga levimbraga 1331 Nov 27 13:20 pipeline.py
   -rw-rw-r-- 1 levimbraga levimbraga 1857 Nov 27 16:56 questions.json
   -rw-rw-r-- 1 levimbraga levimbraga   68 Nov 27 16:56 report.csv
   -rw-rw-r-- 1 levimbraga levimbraga   12 Nov 27 13:20 requirements.txt
   {
     "questions": [
       {
         "id": "q1",
         "question": "How many rows did the orders DataFrame have right after load_orders read orders.csv, before any filtering?",
   ```
2. ```text
   cat pipeline.py report.csv README.md; .venv/bin/ormaos list; .venv/bin/ormaos show last --full; .venv/bin/ormaos tree last --depth 5
   ```

   Output, the 8 lines of 137 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-1.jsonl?plain=1#L6)):

   ```text
   east,4349.29
   - `orders.csv`: one row per order (`order_id`, `customer_id`, `placed`, `amount`), 200 orders of October;
             returned: 200 rows x 4 columns: order_id int64 0 null, customer_id string 0 null, placed str 0 null, amount float64 5 null
             orders: 200 rows x 4 columns: order_id int64 0 null, customer_id string 0 null, placed str 0 null, amount float64 5 null
             returned: 195 rows x 4 columns: order_id int64 0 null, customer_id string 0 null, placed str 0 null, amount float64 0 null
             orders: 195 rows x 4 columns: order_id int64 0 null, customer_id string 0 null, placed str 0 null, amount float64 0 null
             returned: 178 rows x 6 columns: order_id int64 0 null, customer_id string 0 null, placed str 0 null, amount float64 0 null, name str 0 null, region str 0 null
             joined: 178 rows x 6 columns: order_id int64 0 null, customer_id string 0 null, placed str 0 null, amount float64 0 null, name str 0 null, region str 0 null
   ```
3. ```text
   .venv/bin/ormaos io r1 && cat > answers.json <<'EOF'
   {
     "q1": 200,
     "q2": 5,
     "q3": "no",
     "q4": 195,
     "q5": 178,
     "q6": null,
     "q7": "east, 4349.29",
     "q8": 17182.34
   }
   EOF
   ```

   … 1 more line of this command

   Output, the first 15 of 18 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-1.jsonl?plain=1#L15)):

   ```text
   r1: 6 io events (file 6)
     1x file open /sys/fs/cgroup/cpu.max (read) -> raised  at pipeline.py:11 in load_orders  [r1:i1]
     1x file open /sys/fs/cgroup/cpu/cpu.cfs_quota_us (read) -> raised  at pipeline.py:11 in load_orders  [r1:i2]
     1x file open /sys/fs/cgroup/cpu/cpu.cfs_period_us (read) -> raised  at pipeline.py:11 in load_orders  [r1:i3]
     1x file open orders.csv (read)  at pipeline.py:11 in load_orders  [r1:i4]
     1x file open customers.csv (read)  at pipeline.py:15 in load_customers  [r1:i5]
     1x file open report.csv (write)  at pipeline.py:37 in write_report  [r1:i6]
   next: ormaos io r1:i1 | ormaos io r1:i2 | ormaos io r1:c3 | ormaos exceptions r1
   {
       "q1": 200,
       "q2": 5,
       "q3": "no",
       "q4": 195,
       "q5": 178,
       "q6": null,
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `200` |
| q2 | right | `5` |
| q3 | right | `"no"` |
| q4 | right | `195` |
| q5 | right | `178` |
| q6 | null |  |
| q7 | right | `"east, 4349.29"` |
| q8 | right | `17182.34` |

Its own words on q6: the paragraphs of its last message that name it

```text
| id | answer | where it comes from |
|---|---|---|
| q1 | 200 | `load_orders` returned 200 rows × 4 columns |
| q2 | 5 | `amount` had 5 nulls; `drop_unpriced` turned 200 rows into 195 |
| q3 | "no" | there was no call to `drop_repeats` in the recording; `main` called only `load_orders`, `load_customers`, `drop_unpriced`, `join_customers`, `revenue_by_region` and `write_report` |
| q4 | 195 | `join_customers` received 195 rows |
| q5 | 178 | `join_customers` returned 178 rows × 6 columns |
| q6 | null | see below |
| q7 | "east, 4349.29" | first data row of `report.csv` |
| q8 | 17182.34 | 4349.29 + 2567.98 + 6196.49 + 4068.58 |

**Why q6 is null:** the merge went from 195 rows to 178, a drop of 17. That drop equals the number of unmatched orders only if each `customer_id` appears once in `customers.csv`. If an ID appeared twice, the inner merge would duplicate those orders, and more than 17 could have been lost. Ormaos records the row count, column types and nulls of the customers table (40 rows, no nulls), but not its values. So whether the IDs were unique can't be checked, and `customers.csv` is no longer here. If you know the IDs are unique, the answer is 17.
```

#### `ormaos-values`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-values-1.jsonl)
- Score 0.88: 7 right, 1 null, 0 wrong
- 4 tool calls, 70,789 tokens, 27 s

Commands, in order (4):

1. ```text
   cd /srv/data-pipeline; ls -la; cat questions.json; .venv/bin/ormaos guide
   ```

   Output, the first 15 of 179 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-values-1.jsonl?plain=1#L5)):

   ```text
   total 32
   drwxrwxr-x 4 levimbraga levimbraga 4096 Nov 27 16:56 .
   drwx------ 3 levimbraga levimbraga   60 Nov 27 16:58 ..
   drwxrwxr-x 3 levimbraga levimbraga 4096 Nov 27 16:56 .ormaos
   drwxrwxr-x 5 levimbraga levimbraga 4096 Nov 27 13:56 .venv
   -rw-rw-r-- 1 levimbraga levimbraga  637 Nov 27 13:20 README.md
   -rw-rw-r-- 1 levimbraga levimbraga 1331 Nov 27 13:20 pipeline.py
   -rw-rw-r-- 1 levimbraga levimbraga 1857 Nov 27 16:56 questions.json
   -rw-rw-r-- 1 levimbraga levimbraga   68 Nov 27 16:56 report.csv
   -rw-rw-r-- 1 levimbraga levimbraga   12 Nov 27 13:20 requirements.txt
   {
     "questions": [
       {
         "id": "q1",
         "question": "How many rows did the orders DataFrame have right after load_orders read orders.csv, before any filtering?",
   ```
2. ```text
   cd /srv/data-pipeline; cat pipeline.py report.csv README.md; .venv/bin/ormaos list; .venv/bin/ormaos show last --full; .venv/bin/ormaos tree last
   ```

   Output, the 9 lines of 138 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-values-1.jsonl?plain=1#L7)):

   ```text
   east,4349.29
   - `orders.csv`: one row per order (`order_id`, `customer_id`, `placed`, `amount`), 200 orders of October;
   values: recorded in this recording (cut at 200 characters, likely secrets written as ***): it holds data of the program
             returned: 200 rows x 4 columns: order_id int64 0 null, customer_id string 0 null, placed str 0 null, amount float64 5 null
             orders: 200 rows x 4 columns: order_id int64 0 null, customer_id string 0 null, placed str 0 null, amount float64 5 null
             returned: 195 rows x 4 columns: order_id int64 0 null, customer_id string 0 null, placed str 0 null, amount float64 0 null
             orders: 195 rows x 4 columns: order_id int64 0 null, customer_id string 0 null, placed str 0 null, amount float64 0 null
             returned: 178 rows x 6 columns: order_id int64 0 null, customer_id string 0 null, placed str 0 null, amount float64 0 null, name str 0 null, region str 0 null
             joined: 178 rows x 6 columns: order_id int64 0 null, customer_id string 0 null, placed str 0 null, amount float64 0 null, name str 0 null, region str 0 null
   ```
3. ```text
   cd /srv/data-pipeline; .venv/bin/ormaos io last; ls -la .ormaos/r1; .venv/bin/ormaos tree last:c6 --json | head -c 3000
   ```

   Output, the 2 lines of 152 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-values-1.jsonl?plain=1#L14)):

   ```text
             "rows": 195,
           "rows": 178,
   ```
4. ```text
   cd /srv/data-pipeline; cat > answers.json <<'EOF'
   {
     "q1": 200,
     "q2": 5,
     "q3": "no",
     "q4": 195,
     "q5": 178,
     "q6": null,
     "q7": "east, 4349.29",
     "q8": 17182.34
   }
   EOF
   ```

   … 1 more line of this command

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `200` |
| q2 | right | `5` |
| q3 | right | `"no"` |
| q4 | right | `195` |
| q5 | right | `178` |
| q6 | null |  |
| q7 | right | `"east, 4349.29"` |
| q8 | right | `17182.34` |

Its own words on q6: the paragraphs of its last message that name it

```text
I wrote `answers.json` with seven answers taken from the Ormaos recording (`r1`, which finished with exit code 0) and `report.csv`. I left one answer, q6, as null.

| id | answer | source |
|---|---|---|
| q1 | 200 | `load_orders` returned a frame of 200 rows × 4 columns |
| q2 | 5 | `amount` had 5 nulls; `drop_unpriced` went from 200 rows to 195, with 0 nulls left |
| q3 | "no" | there's no `drop_repeats` call in the recorded call tree |
| q4 | 195 | the `orders` argument to `join_customers` had 195 rows |
| q5 | 178 | `join_customers` returned 178 rows × 6 columns |
| q6 | null | see below |
| q7 | "east, 4349.29" | first data row of `report.csv`, which was written by that run |
| q8 | 17182.34 | 4349.29 + 2567.98 + 6196.49 + 4068.58 |

**Why q6 is null:** the inner merge went from 195 rows to 178, a net drop of 17. That net drop only equals the number of unmatched orders if every `customer_id` in `customers.csv` was unique. If some customer appeared twice, matching orders would be doubled in the merge, and more than 17 orders could have gone unmatched. Ormaos records the row and null counts of each table, but not the values or how many are distinct, and `customers.csv` is gone. The README says the file has "one row per customer", but that describes the export, not what this run read. If you trust the README on that point, the answer would be 17.
```

## What Ormaos data answered

Read from the streams: in each run of an Ormaos arm, the `ormaos` verbs in its commands up to its last write of `answers.json`. A question counts for a verb when a run that ran the verb answered it (not null); a run that ran several verbs counts under each of them.

| Question | `ormaos`: verbs (runs) | answered | right | `ormaos-values`: verbs (runs) | answered | right |
|---|---|---|---|---|---|---|
| q1 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 |
| q2 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 |
| q3 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 |
| q4 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 |
| q5 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 |
| q6 | – | 0/3 | 0/3 | show 1, tree 1, io 1, list 1, guide 1 | 1/3 | 1/3 |
| q7 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 |
| q8 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 | show 3, tree 3, io 3, guide 3, list 2 | 3/3 | 3/3 |

## Every run

Every run of every arm.

| Arm | Run | Score | Right | Null | Wrong | `ormaos` verbs before answers.json | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` | 1 | 0.25 | 2 | 6 | 0 | – | 4 | 53,763 | 30 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-none-1.jsonl) |
| `none` | 2 | 0.25 | 2 | 6 | 0 | – | 5 | 60,965 | 26 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-none-2.jsonl) |
| `none` | 3 | 0.25 | 2 | 6 | 0 | – | 4 | 46,701 | 23 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-none-3.jsonl) |
| `raw` | 1 | 0.38 | 3 | 5 | 0 | – | 4 | 52,598 | 27 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-raw-1.jsonl) |
| `raw` | 2 | 0.38 | 3 | 5 | 0 | – | 5 | 68,967 | 29 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-raw-2.jsonl) |
| `raw` | 3 | 0.38 | 3 | 5 | 0 | – | 7 | 94,514 | 43 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-raw-3.jsonl) |
| `ormaos` | 1 | 0.88 | 7 | 1 | 0 | guide, list, show, tree, io | 3 | 51,313 | 26 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-1.jsonl) |
| `ormaos` | 2 | 0.88 | 7 | 1 | 0 | guide, list, show, tree, io | 4 | 67,985 | 26 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-2.jsonl) |
| `ormaos` | 3 | 0.88 | 7 | 1 | 0 | guide, show, tree, io | 4 | 68,105 | 27 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-3.jsonl) |
| `ormaos-values` | 1 | 0.88 | 7 | 1 | 0 | guide, list, show, tree, io | 4 | 70,789 | 27 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-values-1.jsonl) |
| `ormaos-values` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, tree, io | 4 | 68,114 | 26 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-values-2.jsonl) |
| `ormaos-values` | 3 | 0.88 | 7 | 1 | 0 | guide, show, tree, io | 5 | 88,746 | 30 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/data-pipeline-ormaos-values-3.jsonl) |

## The results files

- The benchmark: [knows2](https://ormaos.com/benchmarks/knows2/#data-pipeline)
- Results folder: [`agent-bench/knows2/results/20261127-165801`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801), earlier: bubblewrap, network open
