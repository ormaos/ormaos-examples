# ai-app, in knows2

*Situation · knows2*

A AI app. An app that sends each support ticket to a model API, a local stand-in with a small and a large model, and keeps a one-sentence summary of each ticket. Source: [`use-cases/ai-app`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/use-cases/ai-app).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Mean score over every run: `none` 0.29, `raw` 0.86, `ormaos` 1.00, `ormaos-values` 1.00 (3 runs per arm). Agent: `claude-code / claude-opus-5-5`.

## What happened

5 tickets got a summary from `small-1`, and 3 tickets (403, 405 and 408) from `large-1`. The model server answered 3 of the 11 POST requests with HTTP 503, and `summaries.json` was 703 bytes.

The numbers are the oracle's answers to the questions below: [`oracle/ai-app.json`](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/oracle/ai-app.json).

## What the agent was given

The folder the execution left, with what the arm adds, and 7 questions in `questions.json`, written by a model that was not told about Ormaos. The oracle's answers were not in the folder.

| Question | Asked | Format | The oracle's answer |
|---|---|---|---|
| q2 | How many of the tickets got their summary from the small-1 model, without falling back to large-1? | An integer between 0 and 8 | `5` |
| q3 | How many HTTP 503 ('model overloaded') responses did the model server send during the run? | An integer | `3` |
| q4 | How many POST requests in total did app.py send to the model server, counting both small-1 and large-1 calls? | An integer | `11` |
| q5 | What are the ids of the tickets whose summary came from the large-1 model, in the order they were processed? | A JSON list of the ticket ids exactly as they appear in tickets.json, e.g. [3, 7]; [] if none | `[403, 405, 408]` |
| q6 | What was the length, in characters, of the longest prompt (instruction plus ticket text) that app.py sent in this run? | An integer | `665` |
| q7 | What summary text was written to summaries.json for the first ticket in tickets.json? | The exact summary string, without surrounding quotes | `"The invoice of October shows the old address."` |
| q8 | What was the size, in bytes, of the summaries.json file that this run wrote? | An integer | `703` |

**The prompt of each arm, verbatim**

`none`:

```text
`python3 app.py` ran once in this folder. The folder is as that left it, without the input it read (tickets.json). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out.
```

`raw`:

```text
`python3 app.py` ran once in this folder. The folder is as that left it, without the input it read (tickets.json). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. A VizTracer trace of that execution is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
`python3 app.py` ran once in this folder. The folder is as that left it, without the input it read (tickets.json). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

`ormaos-values`:

```text
`python3 app.py` ran once in this folder. The folder is as that left it, without the input it read (tickets.json). questions.json has questions about what happened in that execution. Write answers.json in this folder: one JSON object with the id of every question as a key and, under it, the answer in the format the question gives. Answer what happened then; give null for an answer you cannot find out. That execution was recorded with Ormaos, values included: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the lines of its output that hold a value the agent wrote in `answers.json`, or its first 15 lines, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-none-1.jsonl)
- Score 0.29: 2 right, 5 null, 0 wrong
- 3 tool calls, 36,204 tokens, 18 s

Commands, in order (3):

1. ```text
   cd /srv/ai-app; ls -la; cat questions.json; cat app.py
   ```
2. ```text
   cd /srv/ai-app; cat model_server.py; cat README.md; cat summaries.json; wc -c summaries.json
   ```
3. ```text
   cd /srv/ai-app; cat > answers.json <<'EOF'
   {
     "q2": null,
     "q3": null,
     "q4": null,
     "q5": null,
     "q6": null,
     "q7": "The invoice of October shows the old address.",
     "q8": 703
   }
   EOF
   python3 -m json.tool answers.json >/dev/null && echo ok
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q2 | null |  |
| q3 | null |  |
| q4 | null |  |
| q5 | null |  |
| q6 | null |  |
| q7 | right | `"The invoice of October shows the old address."` |
| q8 | right | `703` |

Its own words on q2, q3, q4, q5 and q6: the paragraphs of its last message that name them

```text
**Null (q2–q6):** these need the length of each ticket's text. The model server sends a 503 to `small-1` for any prompt over 600 characters, and `app.py` then retries the same prompt with `large-1`. So the ticket lengths would tell me which tickets fell back, how many 503s there were, the total number of POSTs (8 plus one per fallback), and the longest prompt. But `tickets.json` is gone. The server didn't log anything, and `summaries.json` doesn't record which model wrote each summary. Both models produce the same text: the first sentence of the ticket. So there's nothing left to work these out from.
```

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-raw-1.jsonl)
- Score 0.86: 6 right, 1 null, 0 wrong
- 5 tool calls, 75,290 tokens, 39 s

Commands, in order (5):

1. ```text
   cd /srv/ai-app; ls -la; cat questions.json; cat app.py; python3 -c "
   import json;d=json.load(open('result.json'));e=d['traceEvents'];print(len(e));print(e[:3])"
   ```
2. ```text
   cd /srv/ai-app; cat model_server.py README.md summaries.json; wc -c summaries.json; python3 -c "
   import json,collections;d=json.load(open('result.json'));e=d['traceEvents']
   c=collections.Counter(x['name'] for x in e if x.get('ph')=='X');
   for k,v in c.most_common():
     if any(s in k for s in ['app.py','model_server','send_error','send_response','urlopen','HTTPError','json']): print(v,k)
   "
   ```
3. ```text
   cd /srv/ai-app; python3 -c "
   import json;d=json.load(open('result.json'));e=[x for x in d['traceEvents'] if x.get('ph')=='X']
   e.sort(key=lambda x:x['ts'])
   print([k for k in d if k!='traceEvents'])
   S=[x for x in e if x['name'].startswith(('summarize','ask (','HTTPError.__init__','generate'))]
   for x in S: print(x['ts'],x['dur'],x['name'],x.get('args'))
   g=[x for x in e if x['name'].startswith('generate')]
   for x in g:
     inner=[y for y in e if y['ts']>=x['ts'] and y['ts']+y['dur']<=x['ts']+x['dur'] and y['tid']==x['tid'] and y is not x]
     print([ (y['name'],y.get('args')) for y in inner][:6])
   "
   ```
4. ```text
   cd /srv/ai-app; python3 -c "
   import json;d=json.load(open('result.json'));e=[x for x in d['traceEvents'] if x.get('ph')=='X']
   e.sort(key=lambda x:x['ts'])
   print(d['viztracer_metadata'])
   for x in e:
     if x['name'].split(' ')[0] in ('generate','main','<module>','ask','summarize','Handler.do_POST','start','load_tickets','save','builtins.len','HTTPError.__init__','send_response'): print(x['pid'],x['tid'],x['ts'],x['dur'],x['name'])
   " | head -80
   ```
5. ```text
   cd /srv/ai-app; cat > answers.json <<'EOF'
   {"q2": 5, "q3": 3, "q4": 11, "q5": [403, 405, 408], "q6": null, "q7": "The invoice of October shows the old address.", "q8": 703}
   EOF
   python3 -m json.tool answers.json >/dev/null && echo ok
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q2 | right | `5` |
| q3 | right | `3` |
| q4 | right | `11` |
| q5 | right | `[403, 405, 408]` |
| q6 | null |  |
| q7 | right | `"The invoice of October shows the old address."` |
| q8 | right | `703` |

Its own words on q6: the paragraphs of its last message that name it

```text
I've written `answers.json` in `/srv/ai-app`, and it parses as valid JSON. I answered six of the seven questions from the trace and the files the run left behind; q6 is `null`.

| Question | Answer | How I got it |
|---|---|---|
| q2: summaries from small-1 alone | 5 | 8 tickets went through `summarize`, and 3 of them hit an error and fell back. |
| q3: HTTP 503 responses | 3 | There were 3 `HTTPError` calls. The model server only sends 503 when a small-1 prompt is over 600 characters. |
| q4: total POST requests | 11 | There were 11 `ask` calls, 11 `urlopen` calls and 11 server `do_POST` calls. |
| q5: tickets summarized by large-1 | `[403, 405, 408]` | The errors happened inside the 3rd, 5th and 8th `summarize` calls. I matched those positions to the ids in the order they appear in `summaries.json`. |
| q6: longest prompt length | `null` | The trace has no call arguments, and `tickets.json` is missing, so the prompt texts can't be recovered. All that's certain is that the 3 prompts that fell back were each over 600 characters. |
| q7: first ticket's summary | "The invoice of October shows the old address." | From `summaries.json`, entry id 401. |
| q8: size of `summaries.json` | 703 | The file's size on disk. It was last changed at the same time as the trace, so I took it to be this run's output. |
```

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-1.jsonl)
- Score 1.00: 7 right, 0 null, 0 wrong
- 5 tool calls, 86,814 tokens, 28 s

Commands, in order (5):

1. ```text
   ls -la && cat questions.json && .venv/bin/ormaos guide
   ```

   Output, the 1 line of 174 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-1.jsonl?plain=1#L5)):

   ```text
   -rw-rw-r-- 1 levimbraga levimbraga  703 Nov 27 16:57 summaries.json
   ```
2. ```text
   cat app.py model_server.py README.md summaries.json; wc -c summaries.json; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the 5 lines of 200 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-1.jsonl?plain=1#L7)):

   ```text
       "summary": "The invoice of October shows the old address."
   ]703 summaries.json
   r1  2026-11-27 16:57:34  complete  exit 0  662.2ms  1 process, 70 calls, 3 exceptions (3 swallowed), 112 io  .venv/bin/python app.py
   header: format provisional-0, ormaos 0.0.1, mode run, started 2026-11-27 16:57:34, platform linux, in .ormaos/r1
   io: 112 events (file 101, http 11)
   ```
3. ```text
   .venv/bin/ormaos tree r1 --function summarize; .venv/bin/ormaos tree r1 --function ask; .venv/bin/ormaos io r1 --kind http; .venv/bin/ormaos tree r1 --function load_tickets
   ```

   Output, the 4 lines of 31 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-1.jsonl?plain=1#L12)):

   ```text
   r1: 11 of the 70 calls match --function ask (11 ask; 3 raised)
   r1:c20 ask(base: str[22], model: str[7], prompt: str[665]) -> raised  app.py:14  2.1ms  io 1
   r1:c25 ask(base: str[22], model: str[7], prompt: str[665]) -> str[55]  app.py:14  2.0ms  io 1
   r1: 112 io events (file 101, http 11), showing http
   ```
4. ```text
   python3 -I -c "import json;print([(d['id'],len(d['summary'])) for d in json.load(open('summaries.json'))])"; stat -c '%y %s' summaries.json
   ```
5. ```text
   Write answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q2 | right | `5` |
| q3 | right | `3` |
| q4 | right | `11` |
| q5 | right | `[403, 405, 408]` |
| q6 | right | `665` |
| q7 | right | `"The invoice of October shows the old address."` |
| q8 | right | `703` |

#### `ormaos-values`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-values-1.jsonl)
- Score 1.00: 7 right, 0 null, 0 wrong
- 6 tool calls, 117,567 tokens, 31 s

Commands, in order (6):

1. ```text
   cd /srv/ai-app; ls -la; cat questions.json; .venv/bin/ormaos guide
   ```

   Output, the 1 line of 174 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-values-1.jsonl?plain=1#L5)):

   ```text
   -rw-rw-r-- 1 levimbraga levimbraga  703 Nov 27 16:57 summaries.json
   ```
2. ```text
   cd /srv/ai-app; cat app.py model_server.py README.md summaries.json; wc -c summaries.json; .venv/bin/ormaos list; .venv/bin/ormaos show last --full
   ```

   Output, the 5 lines of 201 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-values-1.jsonl?plain=1#L7)):

   ```text
       "summary": "The invoice of October shows the old address."
   ]703 summaries.json
   r1  2026-11-27 16:57:34  complete  exit 0  680.9ms  1 process, 70 calls, 3 exceptions (3 swallowed), 112 io  .venv/bin/python app.py
   header: format provisional-0, ormaos 0.0.1, mode run, started 2026-11-27 16:57:34, platform linux, in .ormaos/r1
   io: 112 events (file 101, http 11)
   ```
3. ```text
   cd /srv/ai-app; .venv/bin/ormaos tree r1 --function summarize --limit 50; .venv/bin/ormaos tree r1 --function ask --limit 50 --json | head -c 6000
   ```

   Output, the 8 lines of 250 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-values-1.jsonl?plain=1#L12)):

   ```text
   r1:c7 summarize(base: str[22]="http://127.0.0.1:35305", ...) -> str[45]="The invoice of October shows the old address."  app.py:24  15.5ms  io 1  calls below: 1
     "matched": 11,
       "ask": 11
           "value": "The invoice of October shows the old address."
             "len": 665,
             "value": "Summarize this support ticket in one sentence.\n\nMy colleague sees the same on her machine. My colleague sees the same on her machine. I tried again this morning and nothing changed. This blocks our mo...[665 characters]"
             "len": 665,
             "value": "Summarize this support ticket in one sentence.\n\nMy colleague sees the same on her machine. My colleague sees the same on her machine. I tried again this morning and nothing changed. This blocks our mo...[665 characters]"
   ```
4. ```text
   cd /srv/ai-app; .venv/bin/ormaos tree r1 --function summarize --json | python3 -c "
   import json,sys;d=json.load(sys.stdin)
   for n in d['nodes']: print(n['address'], json.dumps(n['args']['ticket'])[:200])"
   .venv/bin/ormaos tree r1 --function ask --json | python3 -c "
   import json,sys;d=json.load(sys.stdin)
   for n in d['nodes']: print(n['address'], n['args']['model']['value'], n['args']['prompt']['len'], n['out'])"
   .venv/bin/ormaos tree r1 --function save --json | head -c 3000; .venv/bin/ormaos io r1 --kind file
   ```

   Output, the 8 lines of 137 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-values-1.jsonl?plain=1#L17)):

   ```text
   r1:c7 {"type": "dict", "len": 2, "keys": {"str": 2}, "values": {"int": 1, "str": 1}, "value": {"id": 401, "text": "The invoice of October shows the old address. It worked until the last update. I cleared th
   r1:c19 {"type": "dict", "len": 2, "keys": {"str": 2}, "values": {"int": 1, "str": 1}, "value": {"id": 403, "text": "My colleague sees the same on her machine. My colleague sees the same on her machine. I tri
   r1:c36 {"type": "dict", "len": 2, "keys": {"str": 2}, "values": {"int": 1, "str": 1}, "value": {"id": 405, "text": "It worked until the last update. We are on the team plan since March. I cleared the cache a
   r1:c59 {"type": "dict", "len": 2, "keys": {"str": 2}, "values": {"int": 1, "str": 1}, "value": {"id": 408, "text": "It worked until the last update. This blocks our monthly closing. This blocks our monthly c
   r1:c20 small-1 665 raised
   r1:c25 large-1 665 returned
                 "summary": "The invoice of October shows the old address."
   r1: 112 io events (file 101, http 11), showing file
   ```
5. ```text
   cd /srv/ai-app; .venv/bin/ormaos tree r1 --function save --json | python3 -c "
   import json,sys;d=json.load(sys.stdin);print(len(json.dumps(d['nodes'][0]['args']['summaries']['value'],indent=2).encode()))"
   ```

   Output, the 1 line of 1 that hold a value it wrote in answers.json ([full output](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-values-1.jsonl?plain=1#L22)):

   ```text
   703
   ```
6. ```text
   Write answers.json
   ```

Its answers

| Question | Graded | Answer |
|---|---|---|
| q2 | right | `5` |
| q3 | right | `3` |
| q4 | right | `11` |
| q5 | right | `[403, 405, 408]` |
| q6 | right | `665` |
| q7 | right | `"The invoice of October shows the old address."` |
| q8 | right | `703` |

## What Ormaos data answered

Read from the streams: in each run of an Ormaos arm, the `ormaos` verbs in its commands up to its last write of `answers.json`. A question counts for a verb when a run that ran the verb answered it (not null); a run that ran several verbs counts under each of them.

| Question | `ormaos`: verbs (runs) | answered | right | `ormaos-values`: verbs (runs) | answered | right |
|---|---|---|---|---|---|---|
| q2 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 | show 3, tree 3, guide 3, io 2, list 2 | 3/3 | 3/3 |
| q3 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 | show 3, tree 3, guide 3, io 2, list 2 | 3/3 | 3/3 |
| q4 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 | show 3, tree 3, guide 3, io 2, list 2 | 3/3 | 3/3 |
| q5 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 | show 3, tree 3, guide 3, io 2, list 2 | 3/3 | 3/3 |
| q6 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 | show 3, tree 3, guide 3, io 2, list 2 | 3/3 | 3/3 |
| q7 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 | show 3, tree 3, guide 3, io 2, list 2 | 3/3 | 3/3 |
| q8 | show 3, tree 3, list 3, guide 3, io 2 | 3/3 | 3/3 | show 3, tree 3, guide 3, io 2, list 2 | 3/3 | 3/3 |

## Every run

Every run of every arm.

| Arm | Run | Score | Right | Null | Wrong | `ormaos` verbs before answers.json | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|---|---|---|
| `none` | 1 | 0.29 | 2 | 5 | 0 | – | 3 | 36,204 | 18 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-none-1.jsonl) |
| `none` | 2 | 0.29 | 2 | 5 | 0 | – | 3 | 36,101 | 18 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-none-2.jsonl) |
| `none` | 3 | 0.29 | 2 | 5 | 0 | – | 3 | 36,079 | 17 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-none-3.jsonl) |
| `raw` | 1 | 0.86 | 6 | 1 | 0 | – | 5 | 75,290 | 39 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-raw-1.jsonl) |
| `raw` | 2 | 0.86 | 6 | 1 | 0 | – | 5 | 66,404 | 31 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-raw-2.jsonl) |
| `raw` | 3 | 0.86 | 6 | 1 | 0 | – | 5 | 68,921 | 33 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-raw-3.jsonl) |
| `ormaos` | 1 | 1.00 | 7 | 0 | 0 | guide, list, show, tree, io | 5 | 86,814 | 28 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-1.jsonl) |
| `ormaos` | 2 | 1.00 | 7 | 0 | 0 | guide, list, show, tree | 5 | 86,504 | 28 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-2.jsonl) |
| `ormaos` | 3 | 1.00 | 7 | 0 | 0 | guide, list, show, tree, io | 5 | 89,033 | 30 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-3.jsonl) |
| `ormaos-values` | 1 | 1.00 | 7 | 0 | 0 | guide, list, show, tree, io | 6 | 117,567 | 31 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-values-1.jsonl) |
| `ormaos-values` | 2 | 1.00 | 7 | 0 | 0 | guide, list, show, tree, io | 6 | 108,481 | 30 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-values-2.jsonl) |
| `ormaos-values` | 3 | 1.00 | 7 | 0 | 0 | guide, show, tree | 6 | 112,865 | 31 s | [stream](https://github.com/ormaos/ormaos-examples/blob/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801/streams/ai-app-ormaos-values-3.jsonl) |

## The results files

- The benchmark: [knows2](https://ormaos.com/benchmarks/knows2/#ai-app)
- Results folder: [`agent-bench/knows2/results/20261127-165801`](https://github.com/ormaos/ormaos-examples/tree/091b688f01b0b233631f0fe714935ebc52ab7fd9/agent-bench/knows2/results/20261127-165801)
