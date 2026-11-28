# freight-quote, in knows2

*Situation · knows2*

A scheduled job. A scheduled job that asks a carrier's rate API for the freight of tomorrow's shipments and writes one quote per shipment. Source: [`freight-quote`](https://github.com/ormaos/ormaos-examples/tree/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/freight-quote).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Mean score, per results folder and agent; no number here adds up two of them:

- 2026-11-28, `claude-code / claude-opus-5-5`, controlled: container, network limited to the model host: `none` 1.00, `raw` 1.00, `ormaos` 1.00, `ormaos-values` 1.00 (3 runs per arm)
- 2026-11-27, `claude-code / claude-opus-5-5`, earlier: bubblewrap, network open: `none` 1.00, `raw` 1.00, `ormaos` 1.00, `ormaos-values` 1.00 (3 runs per arm)

## What happened

The run wrote 26 quotes: 9 from the carrier stand-in's answer and 17 from the contract rate card, after the stand-in refused 17 requests with HTTP 429; the first quote from the rate card is `FR-8136`. `calls_used_today` went up by 9, the quotes add up to 114835 cents, and the job printed `quotes finished: OK`.

The numbers are the oracle's answers to the questions below: [`oracle/freight-quote.json`](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/oracle/freight-quote.json).

## What the agent was given

The folder the execution left, with what the arm adds, and 8 questions in `questions.json`, written by a model that was not told about Ormaos. The oracle's answers were not in the folder.

| Question | Asked | Format | The oracle's answer |
|---|---|---|---|
| q1 | How many quote rows did the run write to the quotes table (that is, how many shipments were on the dispatch list it read)? | A non-negative integer, e.g. 42 | `26` |
| q2 | For how many shipments was the written amount_cents the carrier stand-in's answer (an HTTP 200 from /v1/rates), not a price from the contract rate card? | A non-negative integer, e.g. 37 | `9` |
| q3 | For how many shipments did the carrier call fail, so that job.price silently fell back to ratecard.rate (the warning was not printed because the log level defaults to ERROR)? | A non-negative integer, e.g. 5 | `17` |
| q4 | How many of the run's rate requests did the stand-in refuse with HTTP 429 because the account's calls_used_today had reached calls_per_day? | A non-negative integer, e.g. 3 | `17` |
| q5 | What was the shipment_id of the first shipment, in dispatch-list order, whose quote came from the contract rate card instead of the carrier? | A single shipment_id string exactly as written in the dispatch list, or the string "none" if every quote came from the carrier | `"FR-8136"` |
| q6 | Which shipments were refused by the stand-in with HTTP 422 (chargeable weight above 1000 kg) and therefore quoted from the rate card? | A JSON list of shipment_id strings in dispatch-list order, e.g. ["S-104", "S-131"]; [] if none | `[]` |
| q7 | By how much did the run increase calls_used_today in data/carrier.json (each request with the right account and quota left counts, including ones then refused with 404 or 422)? | A non-negative integer, e.g. 40 | `9` |
| q8 | What was the sum of amount_cents over all quote rows the run wrote to the quotes table? | A non-negative integer number of euro cents, e.g. 1234567 | `114835` |

**The prompt of each arm, verbatim**

`none`:

```text
Last night cron ran `python3 job.py` in this folder; since then the dispatch list has been replaced with today's and the carrier's count of calls has started again. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
Last night cron ran `python3 job.py` in this folder; since then the dispatch list has been replaced with today's and the carrier's count of calls has started again. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
Last night cron ran `python3 job.py` in this folder; since then the dispatch list has been replaced with today's and the carrier's count of calls has started again. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
Last night cron ran `python3 job.py` in this folder; since then the dispatch list has been replaced with today's and the carrier's count of calls has started again. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the lines of its output that hold a value the agent wrote in `answers.json`, or its first 15 lines, with a link to the full output in the stream.

### 2026-11-28, `claude-code / claude-opus-5-5`, controlled: container, network limited to the model host

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-none-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 5 tool calls, 91,085 tokens, 41 s

Commands, in order (5):

1. ```text
   cd /srv/freight-quote; ls -la; cat questions.json; cat job.py
   ```
2. ```text
   cd /srv/freight-quote; cat README.md carrier.py quotes.py ratecard.py ratecard.csv shipments.py; ls -la data; cat data/carrier.json; head -5 data/*.csv
   ```
3. ```text
   cd /srv/freight-quote; cat data/cron.log; echo; cat data/booked.csv; echo; cat data/shipments.csv; sqlite3 data/quotes.db "select * from quotes" 2>/dev/null || python3 -I -c "
   import sqlite3;c=sqlite3.connect('data/quotes.db')
   for r in c.execute('select rowid,* from quotes'):print(r)"; ls -la .ormaos seed 2>&1
   ```
4. ```text
   cd /srv/freight-quote; python3 -I -c "
   import sqlite3,json,csv,sys
   sys.path.insert(0,'.')
   from carrier import tariff_price
   import ratecard
   card=ratecard.load()
   t=json.load(open('data/carrier.json'))['tariff']
   b={r['shipment_id']:int(r['charged_cents']) for r in csv.DictReader(open('data/booked.csv'))}
   c=sqlite3.connect('data/quotes.db');s=0
   class S: pass
   for sid,lane,svc,kg,amt,_ in c.execute('select * from quotes order by rowid'):
     x=S();x.lane=lane;x.service=svc;x.chargeable_kg=kg
   ```

   … 3 more lines of this command
5. ```text
   cd /srv/freight-quote; cat > answers.json <<'E'
   {
     "q1": 26,
     "q2": 9,
     "q3": 17,
     "q4": 17,
     "q5": "FR-8136",
     "q6": [],
     "q7": 9,
     "q8": 114835
   }
   E
   ```

   … 1 more line of this command

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `26` |
| q2 | right | `9` |
| q3 | right | `17` |
| q4 | right | `17` |
| q5 | right | `"FR-8136"` |
| q6 | right | `[]` |
| q7 | right | `9` |
| q8 | right | `114835` |

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-raw-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 10 tool calls, 265,302 tokens, 79 s

Commands, in order (10):

1. ```text
   cd /srv/freight-quote; ls -la; cat questions.json; cat job.py
   ```
2. ```text
   cd /srv/freight-quote; cat carrier.py quotes.py ratecard.py ratecard.csv shipments.py README.md; ls -la data; cat data/carrier.json; head -5 data/*.csv
   ```
3. ```text
   cd /srv/freight-quote; cat data/cron.log; cat data/booked.csv; sqlite3 data/quotes.db 'select * from quotes' 2>&1 || python3 -I -c "import sqlite3;[print(r) for r in sqlite3.connect('data/quotes.db').execute('select * from quotes')]"
   ```
4. ```text
   cd /srv/freight-quote; python3 -I -c "
   import json,collections
   d=json.load(open('result.json'))
   ev=d['traceEvents']
   print(len(ev), d.keys())
   c=collections.Counter(e.get('name') for e in ev)
   for n,k in c.items():
     if any(s in n for s in ('job.py','carrier.py','ratecard.py','quotes.py','shipments.py','send_error','do_GET','urlopen','HTTPError')): print(k,n)
   print([e for e in ev if e.get('ph')!='X'][:5])
   "
   ```
5. ```text
   cd /srv/freight-quote; python3 -I -c "
   import json
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X']
   gets=sorted([e for e in ev if 'do_GET' in e['name']],key=lambda e:e['ts'])
   for g in gets:
     kids=[e for e in ev if e['tid']==g['tid'] and g['ts']<=e['ts']<=g['ts']+g['dur'] and e is not g]
     names=[k['name'].split(' ')[0] for k in sorted(kids,key=lambda e:e['ts'])]
     keep=[n for n in names if n in('dumps','tariff_price','send_error','load','loads','open','write','TextIOWrapper.write','float')  or 'write' in n or 'dump' in n or 'tariff' in n or 'send_error' in n]
     print(g['ts'], keep, g.get('args'))
   "
   ```
6. ```text
   cd /srv/freight-quote; python3 -I -c "
   import json
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X']
   g=sorted([e for e in ev if 'do_GET' in e['name']],key=lambda e:e['ts'])[0]
   for e in sorted([e for e in ev if e['tid']==g['tid'] and g['ts']<=e['ts']<=g['ts']+g['dur']],key=lambda e:e['ts']): print(e['ts'],e['dur'],e['name'],e.get('args'))
   print(d['viztracer_metadata'])
   " | head -80
   ```
7. ```text
   cd /srv/freight-quote; python3 -I -c "
   import json
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X']
   gs=sorted([e for e in ev if 'do_GET' in e['name']],key=lambda e:e['ts'])
   g=gs[0]
   for e in sorted([e for e in ev if e['tid']==g['tid'] and g['ts']+100<=e['ts']<=g['ts']+g['dur']],key=lambda e:e['ts'])[:15]: print(e['ts'],e['dur'],e['name'])
   print('---main between')
   rs=sorted([e for e in ev if e['name'].startswith('rate (')],key=lambda e:e['ts'])
   for r in rs[:3]: print(r['ts'],r['dur'],r['name'])
   for e in sorted([e for e in ev if g['ts']+g['dur']<e['ts']<gs[1]['ts'] and e['dur']>1000],key=lambda e:e['ts']): print(e['tid'],e['ts'],e['dur'],e['name'])
   "
   ```
8. ```text
   cd /srv/freight-quote; python3 -I -c "
   import json,collections
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X']
   print(collections.Counter((e['pid'],e['tid']) for e in ev))
   gs=sorted([e for e in ev if 'do_GET' in e['name']],key=lambda e:e['ts'])
   print(gs[0]['pid'],gs[0]['tid'])
   t=[e for e in ev if e['tid']==gs[0]['tid'] and e['pid']==gs[0]['pid']]
   print(min(e['ts'] for e in t), max(e['ts']+e['dur'] for e in t), len(t))
   for e in sorted(t,key=lambda e:-e['dur'])[:8]: print(e['ts'],e['dur'],e['name'])
   print([e for e in d['traceEvents'] if e.get('ph')=='M'])
   "
   ```
9. ```text
   cd /srv/freight-quote; python3 -I -c "
   import json,sqlite3,sys
   sys.path.insert(0,'/srv/freight-quote')
   " ; python3 -I - <<'EOF'
   import json,sqlite3
   d=json.load(open('/srv/freight-quote/result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X']
   for tid in range(4,30):
       t=[e['name'].split(' ')[0] for e in ev if e['tid']==tid]
       kind = '200' if 'tariff_price' in t and 'BaseHTTPRequestHandler.send_error' not in t else ('404' if 'tariff_price' in t else ('422' if '_io.TextIOWrapper.write' in t else 'noinc-err'))
       print(tid, kind, min(e['ts'] for e in ev if e['tid']==tid))
   st=json.load(open('/srv/freight-quote/data/carrier.json'))['tariff']
   ```

   … 14 more lines of this command
10. ```text
   cd /srv/freight-quote; cat > answers.json <<'EOF'
   {"q1": 26, "q2": 9, "q3": 17, "q4": 17, "q5": "FR-8136", "q6": [], "q7": 9, "q8": 114835}
   EOF
   python3 -I -m json.tool answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `26` |
| q2 | right | `9` |
| q3 | right | `17` |
| q4 | right | `17` |
| q5 | right | `"FR-8136"` |
| q6 | right | `[]` |
| q7 | right | `9` |
| q8 | right | `114835` |

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 5 tool calls, 118,584 tokens, 34 s

Commands, in order (5):

1. ```text
   cd /srv/freight-quote; ls -la; cat questions.json; .venv/bin/ormaos guide
   ```

   Output, the 7 lines of 183 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-1.jsonl?plain=1#L3)):

   ```text
   -rw-rw-r-- 1 ubuntu ubuntu 4091 Nov 26 21:12 README.md
   -rw-rw-r-- 1 ubuntu ubuntu 3927 Nov 26 21:13 carrier.py
   -rw-rw-r-- 1 ubuntu ubuntu 2555 Nov 26 21:12 job.py
   -rw-rw-r-- 1 ubuntu ubuntu 2970 Nov 26 21:12 quotes.py
   -rw-rw-r-- 1 ubuntu ubuntu  276 Nov 26 21:12 ratecard.csv
   -rw-rw-r-- 1 ubuntu ubuntu 1039 Nov 26 21:12 ratecard.py
   -rw-rw-r-- 1 ubuntu ubuntu 1959 Nov 26 21:12 shipments.py
   ```
2. ```text
   cd /srv/freight-quote; cat README.md job.py carrier.py quotes.py ratecard.py shipments.py ratecard.csv; ls -la data; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the 4 lines of 535 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-1.jsonl?plain=1#L5)):

   ```text
   r1  2026-11-28 02:47:56  complete  exit 0  644.0ms  1 process, 430 calls, 20 exceptions (17 swallowed), 103 io  .venv/bin/python job.py
   r1 exit 0 in 0.64s: 1 Python process, 430 calls, 20 exceptions (17 swallowed, 0 uncaught, 2 StopIteration taken by the interpreter)
   io: 103 events (file 47, sqlite 30, http 26)
   logs: 19 logging records (WARNING 17, INFO 2), 19 dropped by the level
   ```
3. ```text
   cd /srv/freight-quote; .venv/bin/ormaos io r1 --kind http --limit 100; .venv/bin/ormaos exceptions r1 --limit 100; cat data/cron.log data/carrier.json data/shipments.csv
   ```

   Output, the 2 lines of 109 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-1.jsonl?plain=1#L7)):

   ```text
   r1: 103 io events (file 47, sqlite 30, http 26), showing http
   r1: 20 exceptions (17 swallowed, 0 uncaught, 2 StopIteration taken by the interpreter)
   ```
4. ```text
   cd /srv/freight-quote; python3 -I -c "
   import sqlite3;c=sqlite3.connect('file:data/quotes.db?mode=ro',uri=True)
   for r in c.execute('select rowid,* from quotes order by rowid'):print(r)
   print(c.execute('select count(*),sum(amount_cents) from quotes').fetchall())"; ls -la --time-style=full-iso data .ormaos/r1; .venv/bin/ormaos tree r1 --function price --limit 30
   ```

   Output, the 5 lines of 71 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-1.jsonl?plain=1#L9)):

   ```text
   (10, 'FR-8136', 'MID-STH', 'standard', 16.0, 1528, '2026-11-28T02:47:57+00:00')
   (17, 'FR-8143', 'NTH-WST', 'standard', 75.0, 5590, '2026-11-28T02:47:57+00:00')
   (26, 'FR-8152', 'NTH-STH', 'standard', 40.0, 4250, '2026-11-28T02:47:57+00:00')
   [(26, 114835)]
   r1: 26 of the 430 calls match --function price (26 price; 0 raised)
   ```
5. ```text
   cd /srv/freight-quote; cat > answers.json <<'E'
   {"q1": 26, "q2": 9, "q3": 17, "q4": 17, "q5": "FR-8136", "q6": [], "q7": 9, "q8": 114835}
   E
   cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `26` |
| q2 | right | `9` |
| q3 | right | `17` |
| q4 | right | `17` |
| q5 | right | `"FR-8136"` |
| q6 | right | `[]` |
| q7 | right | `9` |
| q8 | right | `114835` |

#### `ormaos-values`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-values-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 5 tool calls, 112,810 tokens, 35 s

Commands, in order (5):

1. ```text
   cd /srv/freight-quote; ls -la; cat questions.json; .venv/bin/ormaos guide
   ```

   Output, the 7 lines of 183 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-values-1.jsonl?plain=1#L3)):

   ```text
   -rw-rw-r-- 1 ubuntu ubuntu 4091 Nov 26 21:12 README.md
   -rw-rw-r-- 1 ubuntu ubuntu 3927 Nov 26 21:13 carrier.py
   -rw-rw-r-- 1 ubuntu ubuntu 2555 Nov 26 21:12 job.py
   -rw-rw-r-- 1 ubuntu ubuntu 2970 Nov 26 21:12 quotes.py
   -rw-rw-r-- 1 ubuntu ubuntu  276 Nov 26 21:12 ratecard.csv
   -rw-rw-r-- 1 ubuntu ubuntu 1039 Nov 26 21:12 ratecard.py
   -rw-rw-r-- 1 ubuntu ubuntu 1959 Nov 26 21:12 shipments.py
   ```
2. ```text
   cd /srv/freight-quote; cat job.py carrier.py quotes.py ratecard.py shipments.py; ls data; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the 4 lines of 427 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-values-1.jsonl?plain=1#L5)):

   ```text
   r1  2026-11-28 02:47:58  complete  exit 0  661.0ms  1 process, 430 calls, 20 exceptions (17 swallowed), 103 io  .venv/bin/python job.py
   r1 exit 0 in 0.66s: 1 Python process, 430 calls, 20 exceptions (17 swallowed, 0 uncaught, 2 StopIteration taken by the interpreter)
   io: 103 events (file 47, sqlite 30, http 26)
   logs: 19 logging records (WARNING 17, INFO 2), 19 dropped by the level
   ```
3. ```text
   cd /srv/freight-quote; .venv/bin/ormaos io r1 --kind http --limit 100; .venv/bin/ormaos tree r1 --function price --limit 100; .venv/bin/ormaos exceptions r1
   ```

   Output, the 3 lines of 53 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-values-1.jsonl?plain=1#L7)):

   ```text
   r1: 103 io events (file 47, sqlite 30, http 26), showing http
   r1: 26 of the 430 calls match --function price (26 price; 0 raised)
   r1: 20 exceptions (17 swallowed, 0 uncaught, 2 StopIteration taken by the interpreter)
   ```
4. ```text
   cd /srv/freight-quote; .venv/bin/ormaos tree r1:c175; .venv/bin/ormaos exceptions r1:e3; python3 -c "
   import sqlite3;c=sqlite3.connect('file:data/quotes.db?mode=ro',uri=True)
   for r in c.execute('select * from quotes'):print(r)
   print(c.execute('select count(*),sum(amount_cents) from quotes').fetchall())"; ls -la data; cat data/cron.log | tail -20; head -3 data/shipments.csv
   ```

   Output, the 3 lines of 58 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-values-1.jsonl?plain=1#L9)):

   ```text
     same type, same handler: 17 in all: r1:e3 r1:e4 r1:e5 r1:e6 r1:e7 ...
   ('FR-8136', 'MID-STH', 'standard', 16.0, 1528, '2026-11-28T02:47:58+00:00')
   [(26, 114835)]
   ```
5. ```text
   cd /srv/freight-quote; cat > answers.json <<'E'
   {"q1": 26, "q2": 9, "q3": 17, "q4": 17, "q5": "FR-8136", "q6": [], "q7": 9, "q8": 114835}
   E
   cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `26` |
| q2 | right | `9` |
| q3 | right | `17` |
| q4 | right | `17` |
| q5 | right | `"FR-8136"` |
| q6 | right | `[]` |
| q7 | right | `9` |
| q8 | right | `114835` |

### 2026-11-27, `claude-code / claude-opus-5-5`, earlier: bubblewrap, network open

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-none-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 6 tool calls, 120,175 tokens, 44 s

Commands, in order (6):

1. ```text
   cd /srv/freight-quote; ls -la; cat questions.json; cat job.py
   ```
2. ```text
   cd /srv/freight-quote; cat README.md carrier.py quotes.py ratecard.py ratecard.csv shipments.py; ls -la data; cat data/carrier.json; head -5 data/shipments.csv; wc -l data/shipments.csv
   ```
3. ```text
   cd /srv/freight-quote; cat data/cron.log; cat data/booked.csv; cat data/shipments.csv; sqlite3 data/quotes.db 'select * from quotes order by rowid' 2>/dev/null || python3 -I -c "
   import sqlite3;c=sqlite3.connect('data/quotes.db')
   for r in c.execute('select rowid,* from quotes order by rowid'):print(r)"; ls -la ~ / 2>/dev/null | head -40
   ```
4. ```text
   cd /srv/freight-quote; mkdir -p /tmp/an; cat > /tmp/an/a.py <<'EOF'
   import sqlite3,json,csv,sys
   sys.path.insert(0,'/srv/freight-quote')
   import carrier,ratecard
   from types import SimpleNamespace as N
   st=json.load(open('/srv/freight-quote/data/carrier.json'))
   card=ratecard.load()
   bk={r['shipment_id']:int(r['charged_cents']) for r in csv.DictReader(open('/srv/freight-quote/data/booked.csv'))}
   c=sqlite3.connect('/srv/freight-quote/data/quotes.db')
   for sid,lane,svc,kg,amt,_ in c.execute('select * from quotes order by rowid'):
       t=carrier.tariff_price(st['tariff'],lane,kg,svc)
       r=ratecard.rate(card,N(lane=lane,service=svc,chargeable_kg=kg))
   ```

   … 3 more lines of this command
5. ```text
   cd /srv/freight-quote; python3 -I -c "
   import sqlite3;print(sqlite3.connect('data/quotes.db').execute('select count(*),sum(amount_cents) from quotes').fetchone())"
   ```
6. ```text
   Write answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `26` |
| q2 | right | `9` |
| q3 | right | `17` |
| q4 | right | `17` |
| q5 | right | `"FR-8136"` |
| q6 | right | `[]` |
| q7 | right | `9` |
| q8 | right | `114835` |

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-raw-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 7 tool calls, 151,843 tokens, 56 s

Commands, in order (7):

1. ```text
   cd /srv/freight-quote; ls -la; cat questions.json; cat job.py
   ```
2. ```text
   cd /srv/freight-quote; cat carrier.py quotes.py ratecard.py shipments.py ratecard.csv README.md; ls -la data; cat data/carrier.json
   ```
3. ```text
   cd /srv/freight-quote/data; cat cron.log booked.csv shipments.csv; python3 -I -c "
   import sqlite3;c=sqlite3.connect('quotes.db')
   for r in c.execute('select * from quotes'):print(r)
   print(c.execute('select count(*),sum(amount_cents) from quotes').fetchall())"
   ```
4. ```text
   cd /srv/freight-quote; python3 -I -c "
   import json,collections
   d=json.load(open('result.json'))
   ev=d['traceEvents']; print(len(ev), d.keys())
   c=collections.Counter(e.get('name') for e in ev)
   for n,k in c.most_common():
     if any(s in n for s in ['job.py','carrier.py','ratecard.py','quotes.py','shipments.py','send_error','do_GET','send_response','datetime']) : print(k,n)
   print([e for e in ev if e.get('ph')!='X'][:10])
   "
   ```
5. ```text
   cd /srv/freight-quote; python3 -I -c "
   import json
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X']
   gets=sorted([e for e in ev if 'do_GET' in e['name']],key=lambda e:e['ts'])
   for g in gets:
     ch=[e['name'].split(' (')[0] for e in ev if e['tid']==g['tid'] and g['ts']<=e['ts']<=g['ts']+g['dur'] and e is not g]
     inter=[n for n in ch if any(k in n for k in ['tariff_price','send_error','dumps','write','open','send_response'])]
     print(g['ts'],inter, g.get('args'))
   " | head -40
   python3 -I -c "
   import json
   ```

   … 3 more lines of this command
6. ```text
   cd /srv/freight-quote; python3 -I -c "
   import json
   d=json.load(open('result.json'))
   ev=[e for e in d['traceEvents'] if e.get('ph')=='X']
   prices=sorted([e for e in ev if e['name'].startswith('price (')],key=lambda e:e['ts'])
   gets=sorted([e for e in ev if 'do_GET' in e['name']],key=lambda e:e['ts'])
   for i,p in enumerate(prices):
     inn=lambda e:p['ts']<=e['ts']<=p['ts']+p['dur']
     rc=any(e['name'].startswith('rate (/srv/freight-quote/ratecard') and inn(e) for e in ev)
     g=[x for x in gets if inn(x)]
     print(i,p['tid'],p['ts'],p['dur'],'RC' if rc else 'carrier',len(g))
   print(set(e['tid'] for e in gets))
   ```

   … 1 more line of this command
7. ```text
   cd /srv/freight-quote; cat > answers.json <<'E'
   {"q1": 26, "q2": 9, "q3": 17, "q4": 17, "q5": "FR-8136", "q6": [], "q7": 9, "q8": 114835}
   E
   cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `26` |
| q2 | right | `9` |
| q3 | right | `17` |
| q4 | right | `17` |
| q5 | right | `"FR-8136"` |
| q6 | right | `[]` |
| q7 | right | `9` |
| q8 | right | `114835` |

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 5 tool calls, 121,965 tokens, 32 s

Commands, in order (5):

1. ```text
   ls -la && cat questions.json && .venv/bin/ormaos guide
   ```

   Output, the 8 lines of 183 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-1.jsonl?plain=1#L5)):

   ```text
   drwx------ 3 levimbraga levimbraga   60 Nov 27 17:04 ..
   -rw-rw-r-- 1 levimbraga levimbraga 4091 Nov 26 18:12 README.md
   -rw-rw-r-- 1 levimbraga levimbraga 3927 Nov 26 18:13 carrier.py
   -rw-rw-r-- 1 levimbraga levimbraga 2555 Nov 26 18:12 job.py
   -rw-rw-r-- 1 levimbraga levimbraga 2970 Nov 26 18:12 quotes.py
   -rw-rw-r-- 1 levimbraga levimbraga  276 Nov 26 18:12 ratecard.csv
   -rw-rw-r-- 1 levimbraga levimbraga 1039 Nov 26 18:12 ratecard.py
   -rw-rw-r-- 1 levimbraga levimbraga 1959 Nov 26 18:12 shipments.py
   ```
2. ```text
   cat README.md job.py carrier.py quotes.py ratecard.py shipments.py ratecard.csv; ls -la data; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the 4 lines of 535 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-1.jsonl?plain=1#L7)):

   ```text
   r1  2026-11-27 16:57:56  complete  exit 0  649.6ms  1 process, 430 calls, 20 exceptions (17 swallowed), 103 io  .venv/bin/python job.py
   r1 exit 0 in 0.65s: 1 Python process, 430 calls, 20 exceptions (17 swallowed, 0 uncaught, 2 StopIteration taken by the interpreter)
   io: 103 events (file 47, sqlite 30, http 26)
   logs: 19 logging records (WARNING 17, INFO 2), 19 dropped by the level
   ```
3. ```text
   .venv/bin/ormaos io r1 --kind http; .venv/bin/ormaos exceptions r1; cat data/cron.log; cat data/carrier.json; cat data/shipments.csv; cat data/booked.csv
   ```

   Output, the 3 lines of 136 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-1.jsonl?plain=1#L13)):

   ```text
   r1: 103 io events (file 47, sqlite 30, http 26), showing http
   r1: 20 exceptions (17 swallowed, 0 uncaught, 2 StopIteration taken by the interpreter)
   FR-8136,2000
   ```
4. ```text
   python3 -c "
   import sqlite3;c=sqlite3.connect('file:data/quotes.db?mode=ro',uri=True)
   for r in c.execute('select rowid,* from quotes order by rowid'):print(r)
   print(c.execute('select count(*),sum(amount_cents) from quotes').fetchone())"; .venv/bin/ormaos tree r1 --function price --limit 30
   ```

   Output, the 5 lines of 55 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-1.jsonl?plain=1#L20)):

   ```text
   (10, 'FR-8136', 'MID-STH', 'standard', 16.0, 1528, '2026-11-27T19:57:56+00:00')
   (17, 'FR-8143', 'NTH-WST', 'standard', 75.0, 5590, '2026-11-27T19:57:56+00:00')
   (26, 'FR-8152', 'NTH-STH', 'standard', 40.0, 4250, '2026-11-27T19:57:56+00:00')
   (26, 114835)
   r1: 26 of the 430 calls match --function price (26 price; 0 raised)
   ```
5. ```text
   cat > answers.json <<'EOF'
   {"q1": 26, "q2": 9, "q3": 17, "q4": 17, "q5": "FR-8136", "q6": [], "q7": 9, "q8": 114835}
   EOF
   cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `26` |
| q2 | right | `9` |
| q3 | right | `17` |
| q4 | right | `17` |
| q5 | right | `"FR-8136"` |
| q6 | right | `[]` |
| q7 | right | `9` |
| q8 | right | `114835` |

#### `ormaos-values`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-values-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 8 tool calls, 202,552 tokens, 38 s

Commands, in order (8):

1. ```text
   ls -la && cat questions.json && .venv/bin/ormaos guide
   ```

   Output, the 8 lines of 183 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-values-1.jsonl?plain=1#L5)):

   ```text
   drwx------ 3 levimbraga levimbraga   60 Nov 27 17:04 ..
   -rw-rw-r-- 1 levimbraga levimbraga 4091 Nov 26 18:12 README.md
   -rw-rw-r-- 1 levimbraga levimbraga 3927 Nov 26 18:13 carrier.py
   -rw-rw-r-- 1 levimbraga levimbraga 2555 Nov 26 18:12 job.py
   -rw-rw-r-- 1 levimbraga levimbraga 2970 Nov 26 18:12 quotes.py
   -rw-rw-r-- 1 levimbraga levimbraga  276 Nov 26 18:12 ratecard.csv
   -rw-rw-r-- 1 levimbraga levimbraga 1039 Nov 26 18:12 ratecard.py
   -rw-rw-r-- 1 levimbraga levimbraga 1959 Nov 26 18:12 shipments.py
   ```
2. ```text
   cat job.py carrier.py quotes.py ratecard.py shipments.py README.md; ls data; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the 4 lines of 517 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-values-1.jsonl?plain=1#L7)):

   ```text
   r1  2026-11-27 16:57:58  complete  exit 0  671.9ms  1 process, 430 calls, 20 exceptions (17 swallowed), 103 io  .venv/bin/python job.py
   r1 exit 0 in 0.67s: 1 Python process, 430 calls, 20 exceptions (17 swallowed, 0 uncaught, 2 StopIteration taken by the interpreter)
   io: 103 events (file 47, sqlite 30, http 26)
   logs: 19 logging records (WARNING 17, INFO 2), 19 dropped by the level
   ```
3. ```text
   .venv/bin/ormaos tree r1 --function price --limit 100 | head -150; .venv/bin/ormaos io r1 --kind http --limit 100 | head -60
   ```

   Output, the 2 lines of 32 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-values-1.jsonl?plain=1#L12)):

   ```text
   r1: 26 of the 430 calls match --function price (26 price; 0 raised)
   r1: 103 io events (file 47, sqlite 30, http 26), showing http
   ```
4. ```text
   .venv/bin/ormaos tree r1:c175; .venv/bin/ormaos tree r1 --function of --limit 3; .venv/bin/ormaos tree r1 --function read --limit 3
   ```

   Output, the 2 lines of 19 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-values-1.jsonl?plain=1#L17)):

   ```text
   r1: 26 of the 430 calls match --function of (26 Quote.of; 0 raised)
   r1:c17 read(path: pathlib.PosixPath) -> list[26 shipments.Shipment]  shipments.py:56  3.3ms  io 1  calls below: 26
   ```
5. ```text
   .venv/bin/ormaos tree r1:c17 --json | python3 -I -c "
   import json,sys
   d=json.load(sys.stdin)
   print(json.dumps(d)[:3000])"
   ```

   Output, the 1 line of 1 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-values-1.jsonl?plain=1#L22)):

   ```text
   {"kind": "tree", "version": 1, "recording": "r1", "address": "r1:c17", "root": "r1:c17", "ancestors": [{"address": "r1:c1", "file": "job.py", "line": 1, "fn": "<module>"}, {"address": "r1:c15", "file": "job.py", "line": 57, "fn": "main"}], "depth": 2, "limit": 30, "offset": 0, "calls_below_root": 26, "nodes": [{"address": "r1:c17", "file": "shipments.py", "line": 56, "fn": "read", "depth": 0, "args": {"path": {"type": "pathlib.PosixPath"}}, "out": "returned", "duration_s": 0.003327, "thread": 1, "process": 1, "calls_below": 26, "ret": {"type": "list", "len": 26, "items": {"shipments.Shipment": 26}}, "io": 1}, {"address": "r1:c18", "file": "shipments.py", "line": 37, "fn": "parse_row", "depth": 1, "args": {"row": {"type": "dict", "len": 8, "keys": {"str": 8}, "values": {"str": 8}, "value": {"shipment_id": "FR-8127", "origin": "EST", "destination": "EST", "weight_kg": "4", "length_cm": "30", "width_cm": "20", "height_cm": "10", "service": "standard"}}}, "out": "returned", "duration_s": 0.000169, "thread": 1, "process": 1, "calls_below": 1, "ret": {"type": "shipments.Shipment"}}, {"address": "r1:c19", "file": "<string>", "line": 2, "fn": "__create_fn__.<locals>.__init__", "depth": 2, "args": {"self": {"type": "shipments.Shipment"}, "shipment_id": {"type": "str", "len": 7, "value": "FR-8127"}, "origin": {"type": "str", "len": 3, "value": "EST"}, "destination": {"type": "str", "len": 3, "value": "EST"}, "weight_kg": {"type": "float", "value": 4.0}, "length_cm": {"type": "int", "value": 30}, "width_cm": {"type": "int", "value": 20}, "height_cm": {"type": "int", "value": 10}, "service": {"type": "str", "len": 8, "value": "standard"}}, "out": "returned", "duration_s": 6.2e-05, "thread": 1, "process": 1, "calls_below": 0, "ret": {"type": "NoneType", "value": null}}, {"address": "r1:c20", "file": "shipments.py", "line": 37, "fn": "parse_row", "depth": 1, "args": {"row": {"type": "dict", "len": 8, "keys": {"str": 8}, "values": {"str": 8}, "value": {"shipment_id": "FR-8128", "origin": "NTH", "destination": "NTH", "weight_kg": "0.8", "length_cm": "80", "width_cm": "60", "height_cm": "40", "service": "standard"}}}, "out": "returned", "duration_s": 0.000117, "thread": 1, "process": 1, "calls_below": 1, "ret": {"type": "shipments.Shipment"}}, {"address": "r1:c21", "file": "<string>", "line": 2, "fn": "__create_fn__.<locals>.__init__", "depth": 2, "args": {"self": {"type": "shipments.Shipment"}, "shipment_id": {"type": "str", "len": 7, "value": "FR-8128"}, "origin": {"type": "str", "len": 3, "value": "NTH"}, "destination": {"type": "str", "len": 3, "value": "NTH"}, "weight_kg": {"type": "float", "value": 0.8}, "length_cm": {"type": "int", "value": 80}, "width_cm": {"type": "int", "value": 60}, "height_cm": {"type": "int", "value": 40}, "service": {"type": "str", "len": 8, "value": "standard"}}, "out": "returned", "duration_s": 4.3e-05, "thread": 1, "process": 1, "calls_below": 0, "ret": {"type": "NoneType", "value": null}}, {"address": "r1:c22", "file": "shipment
   ```
6. ```text
   .venv/bin/ormaos tree r1:c17 --json --limit 100 | python3 -I -c "
   import json,sys
   d=json.load(sys.stdin)
   ids=[n['args']['row']['value']['shipment_id'] for n in d['nodes'] if n['fn']=='parse_row']
   print(len(ids), ids)"
   .venv/bin/ormaos exceptions r1 --limit 30
   ```

   Output, the 2 lines of 22 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-values-1.jsonl?plain=1#L25)):

   ```text
   26 ['FR-8127', 'FR-8128', 'FR-8129', 'FR-8130', 'FR-8131', 'FR-8132', 'FR-8133', 'FR-8134', 'FR-8135', 'FR-8136', 'FR-8137', 'FR-8138', 'FR-8139', 'FR-8140', 'FR-8141', 'FR-8142', 'FR-8143', 'FR-8144', 'FR-8145', 'FR-8146', 'FR-8147', 'FR-8148', 'FR-8149', 'FR-8150', 'FR-8151', 'FR-8152']
   r1: 20 exceptions (17 swallowed, 0 uncaught, 2 StopIteration taken by the interpreter)
   ```
7. ```text
   python3 -I -c "
   v=[1232,2528,5858,3120,6792,1404,3161,13362,3392,1528,12753,1598,6290,950,3930,2522,5590,5186,4460,1556,10620,1456,3950,1437,5910,4250]
   print(len(v),sum(v))"
   ```
8. ```text
   Write answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `26` |
| q2 | right | `9` |
| q3 | right | `17` |
| q4 | right | `17` |
| q5 | right | `"FR-8136"` |
| q6 | right | `[]` |
| q7 | right | `9` |
| q8 | right | `114835` |

## What Ormaos data answered

Read from the streams: in each run of an Ormaos arm, the `ormaos` verbs in its commands up to its last write of `answers.json`. A question counts for a verb when a run that ran the verb answered it (not null); a run that ran several verbs counts under each of them.

### 2026-11-28, `claude-code / claude-opus-5-5`, controlled: container, network limited to the model host

| Question | `ormaos`: verbs (runs) | answered | right | `ormaos-values`: verbs (runs) | answered | right |
|---|---|---|---|---|---|---|
| q1 | show 3, exceptions 3, io 3, list 3, guide 3, tree 2 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 1 | 3/3 | 3/3 |
| q2 | show 3, exceptions 3, io 3, list 3, guide 3, tree 2 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 1 | 3/3 | 3/3 |
| q3 | show 3, exceptions 3, io 3, list 3, guide 3, tree 2 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 1 | 3/3 | 3/3 |
| q4 | show 3, exceptions 3, io 3, list 3, guide 3, tree 2 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 1 | 3/3 | 3/3 |
| q5 | show 3, exceptions 3, io 3, list 3, guide 3, tree 2 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 1 | 3/3 | 3/3 |
| q6 | show 3, exceptions 3, io 3, list 3, guide 3, tree 2 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 1 | 3/3 | 3/3 |
| q7 | show 3, exceptions 3, io 3, list 3, guide 3, tree 2 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 1 | 3/3 | 3/3 |
| q8 | show 3, exceptions 3, io 3, list 3, guide 3, tree 2 | 3/3 | 3/3 | show 3, tree 3, io 3, list 3, guide 3, exceptions 2, logs 1 | 3/3 | 3/3 |

### 2026-11-27, `claude-code / claude-opus-5-5`, earlier: bubblewrap, network open

| Question | `ormaos`: verbs (runs) | answered | right | `ormaos-values`: verbs (runs) | answered | right |
|---|---|---|---|---|---|---|
| q1 | show 3, exceptions 3, io 3, list 3, guide 3, tree 1 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3 | 3/3 | 3/3 |
| q2 | show 3, exceptions 3, io 3, list 3, guide 3, tree 1 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3 | 3/3 | 3/3 |
| q3 | show 3, exceptions 3, io 3, list 3, guide 3, tree 1 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3 | 3/3 | 3/3 |
| q4 | show 3, exceptions 3, io 3, list 3, guide 3, tree 1 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3 | 3/3 | 3/3 |
| q5 | show 3, exceptions 3, io 3, list 3, guide 3, tree 1 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3 | 3/3 | 3/3 |
| q6 | show 3, exceptions 3, io 3, list 3, guide 3, tree 1 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3 | 3/3 | 3/3 |
| q7 | show 3, exceptions 3, io 3, list 3, guide 3, tree 1 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3 | 3/3 | 3/3 |
| q8 | show 3, exceptions 3, io 3, list 3, guide 3, tree 1 | 3/3 | 3/3 | show 3, tree 3, exceptions 3, io 3, list 3, guide 3 | 3/3 | 3/3 |

## Every run

Every run of every arm, one table per results folder and agent.

### 2026-11-28, `claude-code / claude-opus-5-5`, controlled: container, network limited to the model host

| Arm | Run | Score | Right | Null | Wrong | `ormaos` verbs before answers.json | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` | 1 | 1.00 | 8 | 0 | 0 | – | 5 | 91,085 | 41 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-none-1.jsonl) |
| `none` | 2 | 1.00 | 8 | 0 | 0 | – | 5 | 91,469 | 40 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-none-2.jsonl) |
| `none` | 3 | 1.00 | 8 | 0 | 0 | – | 5 | 91,771 | 45 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-none-3.jsonl) |
| `raw` | 1 | 1.00 | 8 | 0 | 0 | – | 10 | 265,302 | 79 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-raw-1.jsonl) |
| `raw` | 2 | 1.00 | 8 | 0 | 0 | – | 10 | 237,559 | 87 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-raw-2.jsonl) |
| `raw` | 3 | 1.00 | 8 | 0 | 0 | – | 9 | 189,490 | 72 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-raw-3.jsonl) |
| `ormaos` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, io, exceptions, tree | 5 | 118,584 | 34 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-1.jsonl) |
| `ormaos` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, io, exceptions | 5 | 117,866 | 41 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-2.jsonl) |
| `ormaos` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, io, exceptions, tree | 5 | 116,054 | 42 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-3.jsonl) |
| `ormaos-values` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, io, tree, exceptions | 5 | 112,810 | 35 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-values-1.jsonl) |
| `ormaos-values` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, io, tree | 6 | 133,445 | 39 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-values-2.jsonl) |
| `ormaos-values` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, io, exceptions, tree, logs | 6 | 150,968 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641/events/freight-quote-ormaos-values-3.jsonl) |

### 2026-11-27, `claude-code / claude-opus-5-5`, earlier: bubblewrap, network open

| Arm | Run | Score | Right | Null | Wrong | `ormaos` verbs before answers.json | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` | 1 | 1.00 | 8 | 0 | 0 | – | 6 | 120,175 | 44 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-none-1.jsonl) |
| `none` | 2 | 1.00 | 8 | 0 | 0 | – | 5 | 93,621 | 37 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-none-2.jsonl) |
| `none` | 3 | 1.00 | 8 | 0 | 0 | – | 5 | 92,436 | 34 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-none-3.jsonl) |
| `raw` | 1 | 1.00 | 8 | 0 | 0 | – | 7 | 151,843 | 56 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-raw-1.jsonl) |
| `raw` | 2 | 1.00 | 8 | 0 | 0 | – | 8 | 164,720 | 57 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-raw-2.jsonl) |
| `raw` | 3 | 1.00 | 8 | 0 | 0 | – | 10 | 251,138 | 88 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-raw-3.jsonl) |
| `ormaos` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, io, exceptions, tree | 5 | 121,965 | 32 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-1.jsonl) |
| `ormaos` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, io, exceptions | 5 | 119,402 | 36 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-2.jsonl) |
| `ormaos` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, io, exceptions | 5 | 119,174 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-3.jsonl) |
| `ormaos-values` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, tree, io, exceptions | 8 | 202,552 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-values-1.jsonl) |
| `ormaos-values` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, io, tree, exceptions | 7 | 186,298 | 37 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-values-2.jsonl) |
| `ormaos-values` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, exceptions, tree, io | 6 | 149,571 | 32 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/freight-quote-ormaos-values-3.jsonl) |

## The results files

- The benchmark: [knows2](https://ormaos.com/benchmarks/knows2/#freight-quote)
- Results folder: [`agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641`](https://github.com/ormaos/ormaos-examples/tree/d2364198b76a10e9dc4d28a3fbca9e8189ff4c68/agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/20261128-122641): 2026-11-28, `claude-code / claude-opus-5-5`, controlled: container, network limited to the model host
- Results folder: [`agent-bench/knows2/results/20261127-165801`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801): 2026-11-27, `claude-code / claude-opus-5-5`, earlier: bubblewrap, network open
