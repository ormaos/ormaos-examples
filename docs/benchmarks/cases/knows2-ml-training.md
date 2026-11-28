# ml-training, in knows2

*Situation · knows2*

A ML training. A PyTorch model trained on CPU that predicts how long a delivery takes, on data made from a seed; each batch is standardized, and a batch whose loss is not finite is left out. Source: [`use-cases/ml-training`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/ml-training).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Mean score over every run: `none` 1.00, `raw` 1.00, `ormaos` 1.00, `ormaos-values` 1.00 (3 runs per arm). Agent: `claude-code / claude-opus-5-5`.

## What happened

38 batches produced an optimizer update and 2 were left out because their loss was not finite: positions 10, 11. In each batch left out, the `weekend` column had the one value 0.0; 38 batches had both values of it.

The numbers are the oracle's answers to the questions below: [`oracle/ml-training.json`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/oracle/ml-training.json).

## What the agent was given

The folder the execution left, with what the arm adds, and 8 questions in `questions.json`, written by a model that was not told about Ormaos. The oracle's answers were not in the folder.

| Question | Asked | Format | The oracle's answer |
|---|---|---|---|
| q1 | Of the 40 batches counted in the printed "trained 40 steps", how many actually produced an Adam optimizer update (optimizer.step() called)? | integer | `38` |
| q2 | How many batches were skipped because their loss was not a finite number? | integer | `2` |
| q3 | Which batches were skipped because of a non-finite loss? Give their 0-based positions in the order the batches were processed. | JSON list of integers in ascending order, e.g. [3, 17] | `[10, 11]` |
| q4 | Which input feature column caused the skipped batches' losses to be non-finite, because its standard deviation within the batch was zero? | one of: distance, parcels, hour, weekend | `"weekend"` |
| q5 | Across all 320 generated rows, how many rows have the weekend flag set to 1.0? | integer | `92` |
| q6 | The printed "last loss 379.2" is the loss of which batch? Give its 0-based position in the order the batches were processed. | integer | `39` |
| q7 | In the batches that were skipped, what single value did the weekend flag take for all 8 rows? | number with one decimal, e.g. 0.0 | `0.0` |
| q8 | How many of the 40 batches had a weekend flag that varied across their 8 rows (i.e. contained both 0.0 and 1.0)? | integer | `38` |

**The prompt of each arm, verbatim**

`none`:

```text
`.venv/bin/python train.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
`.venv/bin/python train.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
`.venv/bin/python train.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
`.venv/bin/python train.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the lines of its output that hold a value the agent wrote in `answers.json`, or its first 15 lines, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-none-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 5 tool calls, 58,669 tokens, 29 s

Commands, in order (5):

1. ```text
   cd /srv/ml-training; ls -la; cat questions.json
   ```
2. ```text
   cd /srv/ml-training; cat train.py README.md requirements.txt; ls .venv/lib/*/site-packages | head -50
   ```
3. ```text
   mkdir -p /tmp/an && cat > /tmp/an/a.py <<'EOF'
   import sys; sys.path.insert(0,'/srv/ml-training')
   import torch
   from torch import nn
   import train
   torch.manual_seed(0)
   f,m=train.make_data()
   print("weekend ones", int((f[:,3]==1.0).sum()))
   model = nn.Sequential(nn.Linear(4, 16), nn.ReLU(), nn.Linear(16, 1))
   opt = torch.optim.Adam(model.parameters(), lr=0.05)
   skipped=[];varied=0;last=None;upd=0
   for i,(b,t) in enumerate(train.batches(f,m)):
   ```

   … 11 more lines of this command
4. ```text
   cd /srv/ml-training; cat > answers.json <<'EOF'
   {"q1": 38, "q2": 2, "q3": [10, 11], "q4": "weekend", "q5": 92, "q6": 39, "q7": 0.0, "q8": 38}
   EOF
   cat answers.json
   ```
5. ```text
   cd /srv/ml-training; ls -la; rm -rf __pycache__ /tmp/an; ls
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `38` |
| q2 | right | `2` |
| q3 | right | `[10, 11]` |
| q4 | right | `"weekend"` |
| q5 | right | `92` |
| q6 | right | `39` |
| q7 | right | `0.0` |
| q8 | right | `38` |

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-raw-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 5 tool calls, 60,364 tokens, 41 s

Commands, in order (5):

1. ```text
   cd /srv/ml-training; ls -la; cat questions.json; python3 -c "
   import json;d=json.load(open('result.json'));e=d['traceEvents'];print(len(e));print(e[:3])"
   ```
2. ```text
   cd /srv/ml-training; cat train.py README.md; python3 -c "
   import json,collections;d=json.load(open('result.json'));e=d['traceEvents'];print(d.keys(), {k:v for k,v in d.items() if k!='traceEvents'})
   c=collections.Counter(x['name'] for x in e if 'train.py' in x.get('name',''));print(c)
   c=collections.Counter(x['name'] for x in e);print([k for k in c if 'step' in k or 'isfinite' in k or 'Adam' in k][:50])
   "
   ```
3. ```text
   cd /srv/ml-training; sed -n 60,200p train.py; python3 -c "
   import json,collections;d=json.load(open('result.json'));e=[x for x in d['traceEvents'] if x.get('ph')=='X'];e.sort(key=lambda x:x['ts'])
   print(e[0]['ts'],e[-1]['ts'])
   for n in ['train_step','apply_update','standardize','make_data','save_checkpoint','main','batches']:
     m=[x for x in e if x['name'].startswith(n+' ')]; print(n,len(m),[x['name'] for x in m[:1]])
   "
   ```
4. ```text
   cd /srv/ml-training; python3 -c "
   import json;d=json.load(open('result.json'));e=[x for x in d['traceEvents'] if x.get('ph')=='X']
   ts=sorted([x for x in e if x['name'].startswith('train_step ')],key=lambda x:x['ts'])
   au=[x for x in e if x['name'].startswith('apply_update ')]
   sk=[i for i,t in enumerate(ts) if not any(t['ts']<=a['ts']<=t['ts']+t['dur'] for a in au)];print('skipped',sk)
   "
   python3 -I -c "
   import random
   rng=random.Random(5);F=[]
   for _ in range(320):
     d=rng.uniform(1,30);p=rng.randint(1,12);h=rng.randint(8,20);w=1.0 if rng.random()<0.3 else 0.0;F.append([d,p,h,w]);rng.gauss(0,3)
   print(sum(f[3] for f in F))
   ```

   … 6 more lines of this command
5. ```text
   cd /srv/ml-training; cat > answers.json <<'E'
   {"q1": 38, "q2": 2, "q3": [10, 11], "q4": "weekend", "q5": 92, "q6": 39, "q7": 0.0, "q8": 38}
   E
   cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `38` |
| q2 | right | `2` |
| q3 | right | `[10, 11]` |
| q4 | right | `"weekend"` |
| q5 | right | `92` |
| q6 | right | `39` |
| q7 | right | `0.0` |
| q8 | right | `38` |

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 6 tool calls, 119,744 tokens, 41 s

Commands, in order (6):

1. ```text
   cd /srv/ml-training; .venv/bin/ormaos guide; ls -la; cat questions.json
   ```

   Output, the 1 line of 179 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-1.jsonl?plain=1#L5)):

   ```text
   -rw-rw-r-- 1 levimbraga levimbraga   11 Nov 27 13:22 requirements.txt
   ```
2. ```text
   cd /srv/ml-training; cat train.py README.md; .venv/bin/ormaos list; .venv/bin/ormaos show last
   ```

   Output, the 8 lines of 107 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-1.jsonl?plain=1#L7)):

   ```text
       """Distance, parcels, hour of the day and a weekend flag; minutes to deliver."""
           weekend = 1.0 if rng.random() < 0.3 else 0.0
           features.append([distance, parcels, hour, weekend])
           minutes.append(4 * distance + 2 * parcels + 6 * weekend + rng.gauss(0, 3))
   A PyTorch model, trained on CPU, that predicts the minutes a delivery takes from four features: distance, number of parcels, hour of the day and a weekend flag. The data is made by the script, the same every time. Each batch of 8 rows is standardized, the model takes one Adam step per batch, and a batch whose loss is not a finite number is left out. The weights are saved to `model.pt`.
   r1  2026-11-27 16:57:19  complete  exit 0  2.18s  1 process, 203 calls, 0 exceptions (0 swallowed), 10 io  .venv/bin/python train.py
   io: 10 events (file 10)
   tensors: an array or a tensor was an argument or a result 400 times, 10 with NaN or inf: return of standardize at train.py:32  [r1:c56]
   ```
3. ```text
   cd /srv/ml-training; .venv/bin/ormaos tree r1 --function train_step --limit 100 | head -150; .venv/bin/ormaos tree r1 --function apply_update | tail -5
   ```

   Output, the 2 lines of 127 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-1.jsonl?plain=1#L12)):

   ```text
         minutes: shape 8, float32, cpu, nan 0, inf 0, min 11.9655, max 129.572
         minutes: shape 8, float32, cpu, nan 0, inf 0, min 10.0131, max 127.583
   ```
4. ```text
   cd /srv/ml-training; .venv/bin/ormaos tree r1:c55; .venv/bin/ormaos tree r1:c59; .venv/bin/ormaos tree r1 --function apply_update --offset 30
   ```

   Output, the 1 line of 48 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-1.jsonl?plain=1#L21)):

   ```text
   r1: 38 of the 203 calls match --function apply_update (38 apply_update; 0 raised)
   ```
5. ```text
   mkdir -p /tmp/chk && cat > /tmp/chk/gen.py <<'EOF'
   import random
   rng = random.Random(5); rows=[]
   for _ in range(320):
       d=rng.uniform(1,30); p=rng.randint(1,12); h=rng.randint(8,20)
       w=1.0 if rng.random()<0.3 else 0.0
       m=4*d+2*p+6*w+rng.gauss(0,3); rows.append((d,p,h,w,m))
   print("weekend ones", sum(r[3] for r in rows))
   var=0
   for b in range(40):
       br=rows[b*8:b*8+8]; ws={r[3] for r in br}
       var+= len(ws)>1
   ```

   … 5 more lines of this command
6. ```text
   cd /srv/ml-training; cat > answers.json <<'EOF'
   {"q1": 38, "q2": 2, "q3": [10, 11], "q4": "weekend", "q5": 92, "q6": 39, "q7": 0.0, "q8": 38}
   EOF
   .venv/bin/python -I -c "import json;print(json.load(open('answers.json')))"
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `38` |
| q2 | right | `2` |
| q3 | right | `[10, 11]` |
| q4 | right | `"weekend"` |
| q5 | right | `92` |
| q6 | right | `39` |
| q7 | right | `0.0` |
| q8 | right | `38` |

#### `ormaos-values`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-values-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 6 tool calls, 130,419 tokens, 38 s

Commands, in order (6):

1. ```text
   cat questions.json && ls -la && .venv/bin/ormaos guide
   ```

   Output, the 1 line of 179 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-values-1.jsonl?plain=1#L5)):

   ```text
   -rw-rw-r-- 1 levimbraga levimbraga   11 Nov 27 13:22 requirements.txt
   ```
2. ```text
   cat train.py README.md && .venv/bin/ormaos show last --full
   ```

   Output, the 8 lines of 131 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-values-1.jsonl?plain=1#L7)):

   ```text
       """Distance, parcels, hour of the day and a weekend flag; minutes to deliver."""
           weekend = 1.0 if rng.random() < 0.3 else 0.0
           features.append([distance, parcels, hour, weekend])
           minutes.append(4 * distance + 2 * parcels + 6 * weekend + rng.gauss(0, 3))
   A PyTorch model, trained on CPU, that predicts the minutes a delivery takes from four features: distance, number of parcels, hour of the day and a weekend flag. The data is made by the script, the same every time. Each batch of 8 rows is standardized, the model takes one Adam step per batch, and a batch whose loss is not a finite number is left out. The weights are saved to `model.pt`.
   header: format provisional-0, ormaos 0.0.1, mode run, started 2026-11-27 16:57:21, platform linux, in .ormaos/r1
   io: 10 events (file 10)
   tensors: an array or a tensor was an argument or a result 400 times, 10 with NaN or inf: return of standardize at train.py:32  [r1:c56]
   ```
3. ```text
   .venv/bin/ormaos tree r1 --function train_step --limit 100 | head -150; .venv/bin/ormaos tree r1 --function apply_update --limit 100 | head -20
   ```

   Output, the 3 lines of 142 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-values-1.jsonl?plain=1#L12)):

   ```text
         minutes: shape 8, float32, cpu, nan 0, inf 0, min 11.9655, max 129.572
         minutes: shape 8, float32, cpu, nan 0, inf 0, min 10.0131, max 127.583
   r1: 38 of the 203 calls match --function apply_update (38 apply_update; 0 raised)
   ```
4. ```text
   .venv/bin/ormaos tree r1:c55; .venv/bin/ormaos tree r1:c59; .venv/bin/ormaos tree r1 --function make_data
   ```

   Output, the first 15 of 33 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-values-1.jsonl?plain=1#L19)):

   ```text
   inside: r1:c1 <module> > r1:c2 main
   r1:c55 train_step(model: torch.nn.modules.container.Sequential, optimizer: torch.optim.adam.Adam, ...) -> NoneType  train.py:50  642us  calls below: 3
         batch: shape 8x4, float32, cpu, nan 0, inf 0, min 0, max 26.9506
         minutes: shape 8, float32, cpu, nan 0, inf 0, min 14.056, max 116.502
     r1:c56 standardize(batch: Tensor[8x4 float32 cpu]) -> Tensor[8x4 float32 cpu]  train.py:32  59us
           batch: shape 8x4, float32, cpu, nan 0, inf 0, min 0, max 26.9506
           returned: shape 8x4, float32, cpu, nan 8, inf 0, min -1.41653, max 2.45451
     r1:c57 predict(model: torch.nn.modules.container.Sequential, batch: Tensor[8x4 float32 cpu]) -> Tensor[8 float32 cpu]  train.py:36  121us
           batch: shape 8x4, float32, cpu, nan 8, inf 0, min -1.41653, max 2.45451
           returned: shape 8, float32, cpu, nan 8, inf 0
     r1:c58 loss_of(predicted: Tensor[8 float32 cpu], minutes: Tensor[8 float32 cpu]) -> Tensor[scalar float32 cpu]  train.py:40  106us
           predicted: shape 8, float32, cpu, nan 8, inf 0
           minutes: shape 8, float32, cpu, nan 0, inf 0, min 14.056, max 116.502
           returned: shape scalar, float32, cpu, nan 1, inf 0
   next: ormaos tree r1:c2 | ormaos exceptions r1:c55
   ```
5. ```text
   cd /tmp && /srv/ml-training/.venv/bin/python -I -c "
   import random
   rng=random.Random(5);rows=[]
   for _ in range(320):
       d=rng.uniform(1,30);p=rng.randint(1,12);h=rng.randint(8,20);w=1.0 if rng.random()<0.3 else 0.0;rng.gauss(0,3);rows.append((d,p,h,w))
   print(sum(r[3] for r in rows))
   for b in range(40):
       B=rows[b*8:b*8+8]
       for i,n in enumerate('dphw'):
           if len({r[i] for r in B})==1: print(b,n,B[0][i])
   print(sum(1 for b in range(40) if len({r[3] for r in rows[b*8:b*8+8]})==2))
   "
   ```
6. ```text
   Write answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `38` |
| q2 | right | `2` |
| q3 | right | `[10, 11]` |
| q4 | right | `"weekend"` |
| q5 | right | `92` |
| q6 | right | `39` |
| q7 | right | `0.0` |
| q8 | right | `38` |

## What Ormaos data answered

Read from the streams: in each run of an Ormaos arm, the `ormaos` verbs in its commands up to its last write of `answers.json`. A question counts for a verb when a run that ran the verb answered it (not null); a run that ran several verbs counts under each of them.

| Question | `ormaos`: verbs (runs) | answered | right | `ormaos-values`: verbs (runs) | answered | right |
|---|---|---|---|---|---|---|
| q1 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, guide 3, list 2 | 3/3 | 3/3 |
| q2 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, guide 3, list 2 | 3/3 | 3/3 |
| q3 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, guide 3, list 2 | 3/3 | 3/3 |
| q4 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, guide 3, list 2 | 3/3 | 3/3 |
| q5 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, guide 3, list 2 | 3/3 | 3/3 |
| q6 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, guide 3, list 2 | 3/3 | 3/3 |
| q7 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, guide 3, list 2 | 3/3 | 3/3 |
| q8 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, guide 3, list 2 | 3/3 | 3/3 |

## Every run

Every run of every arm.

| Arm | Run | Score | Right | Null | Wrong | `ormaos` verbs before answers.json | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` | 1 | 1.00 | 8 | 0 | 0 | – | 5 | 58,669 | 29 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-none-1.jsonl) |
| `none` | 2 | 1.00 | 8 | 0 | 0 | – | 3 | 37,407 | 24 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-none-2.jsonl) |
| `none` | 3 | 1.00 | 8 | 0 | 0 | – | 4 | 46,997 | 27 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-none-3.jsonl) |
| `raw` | 1 | 1.00 | 8 | 0 | 0 | – | 5 | 60,364 | 41 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-raw-1.jsonl) |
| `raw` | 2 | 1.00 | 8 | 0 | 0 | – | 5 | 62,110 | 41 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-raw-2.jsonl) |
| `raw` | 3 | 1.00 | 8 | 0 | 0 | – | 6 | 73,516 | 51 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-raw-3.jsonl) |
| `ormaos` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, tree | 6 | 119,744 | 41 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-1.jsonl) |
| `ormaos` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, tree | 5 | 99,328 | 34 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-2.jsonl) |
| `ormaos` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, tree | 6 | 121,858 | 40 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-3.jsonl) |
| `ormaos-values` | 1 | 1.00 | 8 | 0 | 0 | guide, show, tree | 6 | 130,419 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-values-1.jsonl) |
| `ormaos-values` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, tree | 6 | 130,928 | 38 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-values-2.jsonl) |
| `ormaos-values` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, tree | 5 | 104,785 | 30 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ml-training-ormaos-values-3.jsonl) |

## The results files

- The benchmark: [knows2](https://ormaos.com/benchmarks/knows2/#ml-training)
- Results folder: [`agent-bench/knows2/results/20261127-165801`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801), earlier: bubblewrap, network open
