# rl-env, in knows2

*Situation · knows2*

A RL environment. A grid world in pure Python, where a courier walks from a depot to a customer, and a loop that runs episodes of it with a seeded policy. Source: [`use-cases/rl-env`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/rl-env).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Mean score over every run: `none` 1.00, `raw` 1.00, `ormaos` 1.00, `ormaos-values` 1.00 (3 runs per arm). Agent: `claude-code / claude-opus-5-5`.

## What happened

19 episodes ended with the courier at the customer, and episode 13 at the step limit; `_arrival_bonus` was called 0 times. Over 363 calls of `env.step()`, 89 moves were blocked by a wall or the edge of the grid, and the highest return of an episode was -6.7.

The numbers are the oracle's answers to the questions below: [`oracle/rl-env.json`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/oracle/rl-env.json).

## What the agent was given

The folder the execution left, with what the arm adds, and 8 questions in `questions.json`, written by a model that was not told about Ormaos. The oracle's answers were not in the folder.

| Question | Asked | Format | The oracle's answer |
|---|---|---|---|
| q1 | Of the 20 episodes, how many ended with the courier at the customer at (5, 5), as opposed to ending because the 30-step limit was reached? | An integer, e.g. 7 | `19` |
| q2 | How many times during the whole execution did GridEnv._arrival_bonus() get called (that is, how many times was the 10.0 arrival reward actually given out)? | An integer, e.g. 7 | `0` |
| q3 | What was the value of env.bumps (the counter of moves blocked by a wall or the grid edge) after all 20 episodes had finished? | An integer, e.g. 7 | `89` |
| q4 | What was the total number of env.step() calls made over all 20 episodes combined? | An integer, e.g. 7 | `363` |
| q5 | Which episode, counting from 1, ended because the 30-step limit was reached rather than at the customer? | An integer episode number from 1 to 20, e.g. 7 | `13` |
| q6 | How many steps did the shortest episode of the run take? | An integer, e.g. 7 | `13` |
| q7 | How many times in the whole run did the policy function choose() return the action "right"? | An integer, e.g. 7 | `162` |
| q8 | What was the highest total return of any single episode in the run? | A decimal number rounded to one decimal place, e.g. -3.4 | `-6.7` |

**The prompt of each arm, verbatim**

`none`:

```text
`python3 run.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
`python3 run.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
`python3 run.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
`python3 run.py` ran once in this folder. The folder is as that left it. questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the lines of its output that hold a value the agent wrote in `answers.json`, or its first 15 lines, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-none-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 4 tool calls, 46,849 tokens, 23 s

Commands, in order (4):

1. ```text
   ls -la && cat questions.json && cat run.py
   ```
2. ```text
   cat env.py README.md
   ```
3. ```text
   mkdir -p /tmp/sim && cat > /tmp/sim/s.py <<'EOF'
   import sys; sys.path.insert(0,'/srv/rl-env')
   import random, run, env as E
   calls={'bonus':0,'right':0}
   ob=E.GridEnv._arrival_bonus
   def b(self): calls['bonus']+=1; return ob(self)
   E.GridEnv._arrival_bonus=b
   rng=random.Random(3); g=E.GridEnv(); res=[]; steps=0
   oc=run.choose
   for i in range(20):
       p=g.reset(); t=0.0; d=False; n=0
       while not d:
   ```

   … 8 more lines of this command
4. ```text
   echo '{"q1":19,"q2":0,"q3":89,"q4":363,"q5":13,"q6":13,"q7":162,"q8":-6.7}' > answers.json && cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `19` |
| q2 | right | `0` |
| q3 | right | `89` |
| q4 | right | `363` |
| q5 | right | `13` |
| q6 | right | `13` |
| q7 | right | `162` |
| q8 | right | `-6.7` |

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-raw-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 4 tool calls, 52,715 tokens, 26 s

Commands, in order (4):

1. ```text
   cd /srv/rl-env; ls -la; cat questions.json; head -c 1500 result.json; echo; wc -c result.json
   ```
2. ```text
   cd /srv/rl-env; cat README.md env.py run.py; python3 -c "
   import json,collections
   d=json.load(open('result.json'))['traceEvents']
   c=collections.Counter(e['name'] for e in d if e.get('ph')=='X')
   for k,v in c.items():
     if '/srv' in k or 'run.py' in k or 'env.py' in k: print(v,k)
   "
   ```
3. ```text
   cd /srv/rl-env; python3 -c "
   import json
   d=[e for e in json.load(open('result.json'))['traceEvents'] if e.get('ph')=='X']
   eps=sorted([e for e in d if e['name'].startswith('run_episode')],key=lambda e:e['ts'])
   st=[e for e in d if e['name'].startswith('GridEnv.step')]
   lim=[e for e in d if e['name'].startswith('ended_at_limit')][0]
   for i,ep in enumerate(eps,1):
     n=sum(ep['ts']<=s['ts']<=ep['ts']+ep['dur'] for s in st)
     print(i,n, ep['ts']<=lim['ts']<=ep['ts']+ep['dur'])
   "
   cat > /tmp/sim.py <<'EOF'
   import sys; sys.path.insert(0,'/srv/rl-env')
   ```

   … 12 more lines of this command
4. ```text
   cd /srv/rl-env; echo '{"q1":19,"q2":0,"q3":89,"q4":363,"q5":13,"q6":13,"q7":162,"q8":-6.7}' > answers.json; cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `19` |
| q2 | right | `0` |
| q3 | right | `89` |
| q4 | right | `363` |
| q5 | right | `13` |
| q6 | right | `13` |
| q7 | right | `162` |
| q8 | right | `-6.7` |

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 6 tool calls, 114,889 tokens, 39 s

Commands, in order (6):

1. ```text
   ls -la && cat questions.json && .venv/bin/ormaos guide
   ```

   Output, the 3 lines of 178 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-1.jsonl?plain=1#L4)):

   ```text
   -rw-rw-r-- 1 levimbraga levimbraga  704 Nov 27 13:30 README.md
   -rw-rw-r-- 1 levimbraga levimbraga 1568 Nov 27 13:23 env.py
   -rw-rw-r-- 1 levimbraga levimbraga 1250 Nov 27 13:22 run.py
   ```
2. ```text
   cat run.py env.py README.md; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the first 15 of 156 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-1.jsonl?plain=1#L6)):

   ```text
   """Run episodes of the grid world with a policy that mostly walks to the goal."""
   
   import random
   
   from env import MOVES, GridEnv
   
   EPISODES = 20
   
   
   def choose(rng, position, goal, explore=0.3):
       if rng.random() < explore:
           return rng.choice(sorted(MOVES))
       if position[0] != goal[0] and rng.random() < 0.5:
           return "right" if goal[0] > position[0] else "left"
       if position[1] != goal[1]:
   ```
3. ```text
   O=.venv/bin/ormaos; $O tree r1 --depth 3 | head -40; for f in ended_at_goal ended_at_limit _arrival_bonus _bump step choose run_episode; do echo "== $f"; $O tree r1 --function $f --limit 3 | head -8; done
   ```

   Output, the 5 lines of 75 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-1.jsonl?plain=1#L12)):

   ```text
   ... 19 of the 21 calls directly below r1:c4 are not shown (19 run_episode): --offset 2
   r1: 19 of the 1969 calls match --function ended_at_goal (19 ended_at_goal; 0 raised)
   r1: 89 of the 1969 calls match --function _bump (89 GridEnv._bump; 0 raised)
   r1: 363 of the 1969 calls match --function step (363 GridEnv.step; 0 raised)
   r1: 363 of the 1969 calls match --function choose (363 choose; 0 raised)
   ```
4. ```text
   O=.venv/bin/ormaos; $O tree r1 --function choose --json --limit 1000 > /tmp/choose.json; $O tree r1 --function run_episode --json --limit 100 > /tmp/ep.json; python3 -c "
   import json
   d=json.load(open('/tmp/choose.json')); print(list(d.keys()))
   print(json.dumps(d,indent=1)[:2500])"
   ```

   Output, the 2 lines of 170 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-1.jsonl?plain=1#L18)):

   ```text
    "matched": 363,
     "choose": 363
   ```
5. ```text
   python3 -c "
   import json
   d=json.load(open('/tmp/choose.json'))
   from collections import Counter
   print(len(d['nodes']), Counter(n['ret']['len'] for n in d['nodes']))
   e=json.load(open('/tmp/ep.json'))
   s=[(n['calls_below']-2)//2 for n in e['nodes']]; print(s, sum(s), min(s))
   "
   cat > /tmp/sim.py <<'EOF'
   import sys; sys.path.insert(0,'/srv/rl-env')
   import random, run
   from env import GridEnv
   ```

   … 15 more lines of this command
6. ```text
   cat > answers.json <<'EOF'
   {"q1": 19, "q2": 0, "q3": 89, "q4": 363, "q5": 13, "q6": 13, "q7": 162, "q8": -6.7}
   EOF
   cat answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `19` |
| q2 | right | `0` |
| q3 | right | `89` |
| q4 | right | `363` |
| q5 | right | `13` |
| q6 | right | `13` |
| q7 | right | `162` |
| q8 | right | `-6.7` |

#### `ormaos-values`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-values-1.jsonl)
- Score 1.00: 8 right, 0 null, 0 wrong
- 7 tool calls, 126,028 tokens, 36 s

Commands, in order (7):

1. ```text
   ls -la && cat questions.json && .venv/bin/ormaos guide
   ```

   Output, the 3 lines of 178 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-values-1.jsonl?plain=1#L5)):

   ```text
   -rw-rw-r-- 1 levimbraga levimbraga  704 Nov 27 13:30 README.md
   -rw-rw-r-- 1 levimbraga levimbraga 1568 Nov 27 13:23 env.py
   -rw-rw-r-- 1 levimbraga levimbraga 1250 Nov 27 13:22 run.py
   ```
2. ```text
   cat run.py env.py README.md; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the first 15 of 157 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-values-1.jsonl?plain=1#L8)):

   ```text
   """Run episodes of the grid world with a policy that mostly walks to the goal."""
   
   import random
   
   from env import MOVES, GridEnv
   
   EPISODES = 20
   
   
   def choose(rng, position, goal, explore=0.3):
       if rng.random() < explore:
           return rng.choice(sorted(MOVES))
       if position[0] != goal[0] and rng.random() < 0.5:
           return "right" if goal[0] > position[0] else "left"
       if position[1] != goal[1]:
   ```
3. ```text
   .venv/bin/ormaos tree r1 --function run_episode --limit 3 ; .venv/bin/ormaos tree r1 --function ended_at_goal --limit 100 | head -50; .venv/bin/ormaos tree r1 --function ended_at_limit
   ```

   Output, the 3 lines of 30 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-values-1.jsonl?plain=1#L11)):

   ```text
   r1: 19 of the 1969 calls match --function ended_at_goal (19 ended_at_goal; 0 raised)
   r1:c1425 ended_at_goal(returns: list[13 float]="[-11.9, -9.7, -9.8, -9.600000000000001, -17.1999999999999...", ...) -> NoneType  run.py:20  16us
   r1:c1969 ended_at_goal(returns: list[19 float]="[-11.9, -9.7, -9.8, -9.600000000000001, -17.1999999999999...", ...) -> NoneType  run.py:20  17us
   ```
4. ```text
   for f in _arrival_bonus _bump step choose ended_at_goal ended_at_limit reset; do .venv/bin/ormaos tree r1 --function $f --limit 1 | head -1; done; .venv/bin/ormaos tree r1 --function ended_at_goal --json --limit 100 | head -c 1500
   ```

   Output, the 6 lines of 89 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-values-1.jsonl?plain=1#L16)):

   ```text
   r1: 89 of the 1969 calls match --function _bump (89 GridEnv._bump; 0 raised)
   r1: 363 of the 1969 calls match --function step (363 GridEnv.step; 0 raised)
   r1: 363 of the 1969 calls match --function choose (363 choose; 0 raised)
   r1: 19 of the 1969 calls match --function ended_at_goal (19 ended_at_goal; 0 raised)
     "matched": 19,
       "ended_at_goal": 19
   ```
5. ```text
   .venv/bin/ormaos tree r1 --function choose --json --limit 1000 > /tmp/ch.json; .venv/bin/ormaos tree r1 --function ended_at_goal --json --limit 100 > /tmp/g.json; .venv/bin/ormaos tree r1 --function ended_at_limit --json > /tmp/l.json; .venv/bin/ormaos tree r1 --function run_episode --json --limit 100 > /tmp/r.json; python3 -I -c "
   import json,collections
   c=json.load(open('/tmp/ch.json'));print(len(c['nodes']),collections.Counter(n['ret'].get('value') for n in c['nodes']))
   t=[n['args']['total']['value'] for f in ['/tmp/g.json','/tmp/l.json'] for n in json.load(open(f))['nodes']];print(t, max(t))
   r=json.load(open('/tmp/r.json'));print([n['calls_below'] for n in r['nodes']])
   "
   ```

   Output, the 2 lines of 3 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-values-1.jsonl?plain=1#L21)):

   ```text
   363 Counter({'right': 162, 'down': 148, 'up': 30, 'left': 23})
   [-11.9, -9.7, -9.8, -9.600000000000001, -17.199999999999996, -8.2, -6.699999999999999, -13.9, -13.199999999999998, -8.8, -12.3, -9.1, -7.800000000000001, -9.4, -9.9, -10.400000000000002, -8.4, -9.1, -6.9, -18.7] -6.699999999999999
   ```
6. ```text
   .venv/bin/ormaos tree r1 --function step --json --limit 1000 > /tmp/s.json; python3 -I -c "
   import json,bisect
   s=[int(n['address'].split(':c')[1]) for n in json.load(open('/tmp/s.json'))['nodes']]
   r=[int(n['address'].split(':c')[1]) for n in json.load(open('/tmp/r.json'))['nodes']]
   c=[0]*20
   for a in s: c[bisect.bisect(r,a)-1]+=1
   print(c,sum(c),min(c))
   "
   ```

   Output, the 1 line of 1 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-values-1.jsonl?plain=1#L27)):

   ```text
   [17, 15, 17, 16, 26, 14, 13, 23, 21, 18, 20, 17, 30, 15, 17, 19, 22, 15, 14, 14] 363 13
   ```
7. ```text
   Write answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q1 | right | `19` |
| q2 | right | `0` |
| q3 | right | `89` |
| q4 | right | `363` |
| q5 | right | `13` |
| q6 | right | `13` |
| q7 | right | `162` |
| q8 | right | `-6.7` |

## What Ormaos data answered

Read from the streams: in each run of an Ormaos arm, the `ormaos` verbs in its commands up to its last write of `answers.json`. A question counts for a verb when a run that ran the verb answered it (not null); a run that ran several verbs counts under each of them.

| Question | `ormaos`: verbs (runs) | answered | right | `ormaos-values`: verbs (runs) | answered | right |
|---|---|---|---|---|---|---|
| q1 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 |
| q2 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 |
| q3 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 |
| q4 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 |
| q5 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 |
| q6 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 |
| q7 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 |
| q8 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 | show 3, tree 3, list 3, guide 3 | 3/3 | 3/3 |

## Every run

Every run of every arm.

| Arm | Run | Score | Right | Null | Wrong | `ormaos` verbs before answers.json | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` | 1 | 1.00 | 8 | 0 | 0 | – | 4 | 46,849 | 23 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-none-1.jsonl) |
| `none` | 2 | 1.00 | 8 | 0 | 0 | – | 4 | 47,025 | 23 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-none-2.jsonl) |
| `none` | 3 | 1.00 | 8 | 0 | 0 | – | 4 | 46,653 | 22 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-none-3.jsonl) |
| `raw` | 1 | 1.00 | 8 | 0 | 0 | – | 4 | 52,715 | 26 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-raw-1.jsonl) |
| `raw` | 2 | 1.00 | 8 | 0 | 0 | – | 4 | 55,160 | 28 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-raw-2.jsonl) |
| `raw` | 3 | 1.00 | 8 | 0 | 0 | – | 4 | 52,730 | 25 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-raw-3.jsonl) |
| `ormaos` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, tree | 6 | 114,889 | 39 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-1.jsonl) |
| `ormaos` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, tree | 8 | 151,201 | 48 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-2.jsonl) |
| `ormaos` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, tree | 6 | 113,178 | 37 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-3.jsonl) |
| `ormaos-values` | 1 | 1.00 | 8 | 0 | 0 | guide, list, show, tree | 7 | 126,028 | 36 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-values-1.jsonl) |
| `ormaos-values` | 2 | 1.00 | 8 | 0 | 0 | guide, list, show, tree | 6 | 105,370 | 33 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-values-2.jsonl) |
| `ormaos-values` | 3 | 1.00 | 8 | 0 | 0 | guide, list, show, tree | 6 | 106,909 | 32 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/rl-env-ormaos-values-3.jsonl) |

## The results files

- The benchmark: [knows2](https://ormaos.com/benchmarks/knows2/#rl-env)
- Results folder: [`agent-bench/knows2/results/20261127-165801`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801), earlier: bubblewrap, network open
