# points-grant, in fix

*Situation · fix*

A scheduled job. By its README, it grants loyalty points for purchases. Source: [`agent-bench/bugs/points-grant/task`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/bugs/points-grant/task).

Ormaos records and shows what happened inside your Python execution — the runtime context for your agent and for you.

Passed the check, first attempts: `none` 3/3, `raw` 3/3, `ormaos` 3/3 (3 runs per arm). Agent: `claude-code / claude-opus-5-5`.

## What happened

That night cron ran `python3 job.py`; it printed `points finished: OK` and exited with code 0. This morning the points of 5 members are not the sum of their grants: `M-1042`, `M-1043`, `M-1050`, `M-1051` and `M-1052`. Where it behaved otherwise than its README: an SQL statement that also writes other rows.

The items are those the scenario's own check of the data found, in [`build.json`](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/build.json).

The symptom, from `TASK.md` in the agent's folder:

```text
Last night's points run said OK, but this morning the points of some members are not the sum of their grants (python3 members.py --check).
```

## What the agent was given

Its folder (the code, its README, `TASK.md` and the data that night left, with what the arm adds) and the task text, the same in every arm but for the arm's last sentence:

`none`:

```text
Last night's points run said OK, but this morning the points of some members are not the sum of their grants (python3 members.py --check). The job runs from cron with `python3 job.py`. Find the cause and fix it.
```

`raw`:

```text
Last night's points run said OK, but this morning the points of some members are not the sum of their grants (python3 members.py --check). The job runs from cron with `python3 job.py`. Find the cause and fix it. A VizTracer trace of that run is in result.json, in the Chrome Trace Event format (JSON; "traceEvents" has one entry per function call, with its name, its start "ts" and its duration "dur" in microseconds); read it with python3.
```

`ormaos`:

```text
Last night's points run said OK, but this morning the points of some members are not the sum of their grants (python3 members.py --check). The job runs from cron with `python3 job.py`. Find the cause and fix it. That run was recorded with Ormaos: the recording is in .ormaos/ and the command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.
```

## Run 1 of each arm, side by side

Run 1 of each arm, always run 1: a fixed rule, not a choice. Each column lists the agent's tool calls in order; under each `ormaos` command, the first 15 lines of its output, with a link to the full output in the stream.

#### `none`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-none-1.jsonl)
- Passed the check
- 6 tool calls, 90,447 tokens, 45 s

Commands, in order (6):

1. ```text
   ls -la && cat *.py | head -300
   ```
2. ```text
   cat README.md TASK.md; ls -la data inbox; python3 members.py --check; sqlite3 data/members.db "select email, count(*) from members group by email having count(*)>1; select * from members where email in (select email from members group by email having count(*)>1) or email='';" 2>&1 | head -40
   ```
3. ```text
   cat data/cron.log; python3 -c "
   import sqlite3;c=sqlite3.connect('data/members.db')
   for r in c.execute('select * from members order by email, member_id'):print(r)
   print()
   for r in c.execute('select * from grants order by granted_on, purchase_id'):print(r)
   "
   ```
4. ```text
   Edit members.py
   ```
5. ```text
   T=$(mktemp -d) && cp data/members.db $T/db && mkdir $T/inbox && printf 'purchase_id,member_id,email,amount_cents,store\nT-1,,casa.mota@example.org,1000,old\nT-2,M-1043,casa.mota@example.org,2000,new\n' > $T/inbox/purchases-20261127.csv && python3 -c "
   import sqlite3;c=sqlite3.connect('$T/db');c.execute('UPDATE members SET points=(SELECT COALESCE(SUM(points),0) FROM grants g WHERE g.member_id=members.member_id)');c.commit()" && python3 job.py --inbox $T/inbox --db $T/db && python3 members.py --db $T/db --check && echo "check clean" && python3 members.py --db $T/db | grep Mota; rm -rf $T
   ```
6. ```text
   cp -p data/members.db data/members.db.bak-20261126 && python3 -c "
   import sqlite3;c=sqlite3.connect('data/members.db')
   with c: n=c.execute('UPDATE members SET points=(SELECT COALESCE(SUM(points),0) FROM grants g WHERE g.member_id=members.member_id) WHERE points != (SELECT COALESCE(SUM(points),0) FROM grants g WHERE g.member_id=members.member_id)').rowcount
   print('repaired',n)" && python3 members.py --check && echo "check clean" && python3 members.py | grep -E 'Mota|Brito'
   ```

Its change, against `task/`

```text
--- task/members.py
+++ members.py
@@ -85,8 +85,8 @@
             (purchase.purchase_id, member_id, points, day.isoformat()),
         )
         conn.execute(
-            "UPDATE members SET points = points + ? WHERE member_id = ? OR email = ?",
-            (points, purchase.member_id, purchase.email),
+            "UPDATE members SET points = points + ? WHERE member_id = ?",
+            (points, member_id),
         )
     return points
 
```

What the check said

```text
pass  members who share an address buy: exit 0, members with other points: none, grants as expected
pass  nobody who shares an address buys: exit 0, members with other points: none, grants as expected
fixed
```

#### `raw`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-raw-1.jsonl)
- Passed the check
- 6 tool calls, 89,029 tokens, 42 s

Commands, in order (6):

1. ```text
   ls -la && wc -c *.py && cat *.py
   ```
2. ```text
   cat README.md TASK.md; ls -la data inbox; python3 members.py --check; sqlite3 data/members.db "select email,count(*) from members group by email having count(*)>1" 2>&1 | head; python3 -I -c "
   import json,collections
   d=json.load(open('result.json'))['traceEvents']
   c=collections.Counter(e.get('name') for e in d)
   for k,v in c.most_common(40): print(v,k)
   "
   ```
3. ```text
   cat data/cron.log; python3 -I -c "
   import json
   d=json.load(open('result.json'))['traceEvents']
   for e in sorted(d,key=lambda e:e.get('ts',0)):
     n=e.get('name','')
     if any(k in n for k in ('job.py','members.py','purchases.py','sqlite3','unlink','glob')): print(e.get('ts'),e.get('dur'),n,e.get('args',''))
   " | head -80; python3 -I -c "
   import sqlite3;c=sqlite3.connect('file:data/members.db?mode=ro',uri=True)
   for r in c.execute('select * from members order by member_id'):print(r)
   for r in c.execute('select * from grants order by member_id, granted_on'):print(r)
   "
   ```
4. ```text
   Edit members.py
   ```
5. ```text
   cp -p data/members.db data/members.db.bak-2026-11-26 && python3 -I -c "
   import sqlite3;c=sqlite3.connect('data/members.db')
   with c:
     n=c.execute('UPDATE members SET points=(SELECT COALESCE(SUM(points),0) FROM grants g WHERE g.member_id=members.member_id) WHERE points != (SELECT COALESCE(SUM(points),0) FROM grants g WHERE g.member_id=members.member_id)').rowcount
   print('repaired',n)
   " && python3 members.py --check && echo "check clean" && python3 members.py | grep -E 'M-104[23]|M-105[012]'
   ```
6. ```text
   cd /tmp && rm -rf pgtest && mkdir -p pgtest/inbox && cd pgtest && python3 -c "
   import sys; sys.path.insert(0,'/srv/points-grant')
   import members
   c=members.connect('t.db')
   c.executemany('INSERT INTO members VALUES (?,?,?,?,0)',[('A','a','h@x','silver'),('B','b','h@x','gold')])
   c.commit()
   open('inbox/purchases-20261126.csv','w').write('purchase_id,member_id,email,amount_cents,store\n1,A,h@x,1000,s\n2,B,h@x,2000,s\n3,,h@x,700,s\n')
   import job; print(job.main(['--inbox','inbox','--db','t.db']))
   print(c.execute('select member_id,points from members').fetchall(), members.unbalanced(c))
   "
   ```

Its change, against `task/`

```text
--- task/members.py
+++ members.py
@@ -85,8 +85,9 @@
             (purchase.purchase_id, member_id, points, day.isoformat()),
         )
         conn.execute(
-            "UPDATE members SET points = points + ? WHERE member_id = ? OR email = ?",
-            (points, purchase.member_id, purchase.email),
+            # Only the member found above: household members share an e-mail.
+            "UPDATE members SET points = points + ? WHERE member_id = ?",
+            (points, member_id),
         )
     return points
 
```

What the check said

```text
pass  members who share an address buy: exit 0, members with other points: none, grants as expected
pass  nobody who shares an address buys: exit 0, members with other points: none, grants as expected
fixed
```

#### `ormaos`

- Run 1, [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-ormaos-1.jsonl)
- Passed the check
- 7 tool calls, 97,164 tokens, 47 s

Commands, in order (7):

1. ```text
   ls -la && .venv/bin/ormaos guide
   ```

   Output, the first 15 of 62 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-ormaos-1.jsonl?plain=1#L5)):

   ```text
   total 44
   drwxrwxr-x 6 levimbraga levimbraga 4096 Nov 26 22:17 .
   drwx------ 3 levimbraga levimbraga   60 Nov 26 22:17 ..
   drwxrwxr-x 3 levimbraga levimbraga 4096 Nov 26 22:06 .ormaos
   drwxrwxr-x 5 levimbraga levimbraga 4096 Nov 26 22:06 .venv
   -rw-rw-r-- 1 levimbraga levimbraga 2309 Nov 26 18:46 README.md
   -rw-rw-r-- 1 levimbraga levimbraga  139 Nov 26 22:06 TASK.md
   drwxrwxr-x 2 levimbraga levimbraga 4096 Nov 26 22:06 data
   drwxrwxr-x 2 levimbraga levimbraga 4096 Nov 26 22:06 inbox
   -rw-rw-r-- 1 levimbraga levimbraga 2225 Nov 26 18:47 job.py
   -rw-rw-r-- 1 levimbraga levimbraga 4122 Nov 26 18:46 members.py
   -rw-rw-r-- 1 levimbraga levimbraga  924 Nov 26 18:46 purchases.py
   ormaos: what happened inside a Python run, to read instead of guessing.
   
   WHEN TO USE IT
   ```
2. ```text
   cat TASK.md README.md job.py members.py purchases.py; ls data inbox; .venv/bin/ormaos show
   ```

   Output, the first 15 of 300 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-ormaos-1.jsonl?plain=1#L7)):

   ````text
   Last night's points run said OK, but this morning the points of some members are not the sum of their grants (python3 members.py --check).
   # points-grant
   
   A scheduled job that grants loyalty points: the tills' export drops the day's purchases in `inbox/` every evening, and at night the job grants each member the points of their purchases, so that the app shows them in the morning.
   
   It uses only the Python standard library (Python 3.12 or newer). The folder is self-contained: copy it anywhere and it runs.
   
   ## Run it
   
   ```bash
   python3 job.py              # grant the purchases in inbox/
   python3 members.py          # show the members and their points
   python3 members.py --check  # members whose points are not the sum of their grants
   ```
   
   ````
3. ```text
   python3 members.py --check; cat data/cron.log; .venv/bin/ormaos io r1 | head -40; sqlite3 data/members.db "select email, group_concat(member_id) from members group by email having count(*)>1" 2>&1
   ```

   Output, the first 15 of 24 lines ([full output](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-ormaos-1.jsonl?plain=1#L12)):

   ```text
   Exit code 127
   M-1042  Carla Mota: 1546 points, grants add up to 1528
   M-1043  Diogo Mota: 326 points, grants add up to 78
   M-1050  Lara Brito: 561 points, grants add up to 505
   M-1051  Marco Brito: 16 points, grants add up to 151
   M-1052  Nuno Brito: -67 points, grants add up to 12
   2026-11-26T22:06:56 points-grant exit=0 points finished: OK
   2026-11-26T22:06:56 points-grant exit=0 points finished: OK
   r1: 73 io events (sqlite 72, file 1)
     1x sqlite connect data/members.db  at members.py:36 in connect  [r1:i1]
     1x sqlite CREATE TABLE IF NOT EXISTS members ( member_id TEXT PRIMARY KEY, name...  at members.py:37 in connect  [r1:i2]
     1x sqlite CREATE TABLE IF NOT EXISTS grants ( purchase_id TEXT PRIMARY KEY, mem...  at members.py:37 in connect  [r1:i3]
     1x file open inbox/purchases-20261125.csv (read)  at purchases.py:23 in read  [r1:i4]
     13x sqlite SELECT ? FROM grants WHERE purchase_id = ?  at members.py:71 in grant  [r1:i5]
     10x sqlite SELECT member_id, tier, points FROM members WHERE member_id = ?  at members.py:47 in find  [r1:i7]
   ```
4. ```text
   python3 -c "
   import sqlite3;c=sqlite3.connect('data/members.db')
   for r in c.execute('select * from members order by member_id'):print(r)
   print()
   for r in c.execute('select * from grants order by granted_on, purchase_id'):print(r)
   "
   ```
5. ```text
   Edit members.py
   ```
6. ```text
   cp data/members.db data/members.db.bak-20261126 && python3 -c "
   import sqlite3;c=sqlite3.connect('data/members.db')
   with c:
     c.execute('''UPDATE members SET points=(SELECT COALESCE(SUM(points),0) FROM grants g WHERE g.member_id=members.member_id)
      WHERE member_id IN ('M-1042','M-1043','M-1050','M-1051','M-1052')''')
   for r in c.execute(\"select member_id,name,points from members where member_id in ('M-1042','M-1043','M-1050','M-1051','M-1052')\"):print(r)
   " && python3 members.py --check && echo CHECK-CLEAN
   ```
7. ```text
   T=$(mktemp -d) && cp data/members.db $T/db && mkdir $T/inbox && printf 'purchase_id,member_id,email,amount_cents,store\nT-1,M-1043,casa.mota@example.org,2500,Porto\nT-2,,familia.brito@example.org,1000,Braga\nT-3,M-1052,familia.brito@example.org,-9000,Braga\n' > $T/inbox/purchases-20261126.csv && python3 job.py --inbox $T/inbox --db $T/db && python3 members.py --db $T/db | grep -E 'Mota|Brito' && python3 members.py --db $T/db --check && echo CHECK-CLEAN; rm -r $T
   ```

Its change, against `task/`

```text
--- task/members.py
+++ members.py
@@ -85,8 +85,10 @@
             (purchase.purchase_id, member_id, points, day.isoformat()),
         )
         conn.execute(
-            "UPDATE members SET points = points + ? WHERE member_id = ? OR email = ?",
-            (points, purchase.member_id, purchase.email),
+            # Only the member found above: household members share an e-mail
+            # address, and a purchase from an older till has no member_id.
+            "UPDATE members SET points = points + ? WHERE member_id = ?",
+            (points, member_id),
         )
     return points
 
```

What the check said

```text
pass  members who share an address buy: exit 0, members with other points: none, grants as expected
pass  nobody who shares an address buys: exit 0, members with other points: none, grants as expected
fixed
```

## Every run

The first attempt of every run of every arm.

| Arm | Run | Check | Last line | Tool calls | Tokens | Wall time | Stream |
|---|---|---|---|---|---|---|---|
| `none` | 1 | passed | `fixed` | 6 | 90,447 | 45 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-none-1.jsonl) |
| `none` | 2 | passed | `fixed` | 6 | 78,831 | 48 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-none-2.jsonl) |
| `none` | 3 | passed | `fixed` | 6 | 73,135 | 42 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-none-3.jsonl) |
| `raw` | 1 | passed | `fixed` | 6 | 89,029 | 42 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-raw-1.jsonl) |
| `raw` | 2 | passed | `fixed` | 8 | 141,928 | 55 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-raw-2.jsonl) |
| `raw` | 3 | passed | `fixed` | 7 | 107,074 | 51 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-raw-3.jsonl) |
| `ormaos` | 1 | passed | `fixed` | 7 | 97,164 | 47 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-ormaos-1.jsonl) |
| `ormaos` | 2 | passed | `fixed` | 7 | 94,764 | 44 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-ormaos-2.jsonl) |
| `ormaos` | 3 | passed | `fixed` | 5 | 63,866 | 35 s | [stream](https://github.com/ormaos/ormaos-examples/blob/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703/streams/points-grant-ormaos-3.jsonl) |

## The results files

- The benchmark: [fix](https://ormaos.com/benchmarks/fix/)
- Results folder: [`agent-bench/results/20261126-220703`](https://github.com/ormaos/ormaos-examples/tree/88bec53c78471c6086564b4de8a00084c4dc4ae6/agent-bench/results/20261126-220703)
