# agent-bench: fixes per arm

N = 72 runs, the first attempt of every bug, arm and run; all of them count. 8 bugs x 3 arms x 3 runs. Model: claude-opus-5-5. Ormaos 75c191a, VizTracer 1.1.1, Python 3.14.4; built 2026-11-26T22:06:14.

Fixed means that the bug's `hidden/check.py` passed on the code the agent left. The interval is the 95% Wilson score interval.

| Arm | Fixed | 95% interval | Median wall time | Median tool calls | Median tokens | Timed out |
|---|---|---|---|---|---|---|
| none | 21/24 | 69% to 96% | 50 s | 7 | 94,458 | 0 |
| raw | 23/24 | 80% to 99% | 56 s | 8 | 140,558 | 0 |
| ormaos | 24/24 | 86% to 100% | 44 s | 7 | 112,676 | 0 |

Tokens are input, output and cache tokens added up, as the claude command line reports them.

At this size the difference is within the margin: the 95% intervals of the arms overlap, so these runs do not show that one arm fixes more bugs than another.

## Per bug

| Bug | none | raw | ormaos |
|---|---|---|---|
| commission-run | 3/3 (44%-100%) | 3/3 (44%-100%) | 3/3 (44%-100%) |
| freight-quote | 3/3 (44%-100%) | 3/3 (44%-100%) | 3/3 (44%-100%) |
| fx-rates | 1/3 (6%-79%) | 3/3 (44%-100%) | 3/3 (44%-100%) |
| late-fees | 2/3 (21%-94%) | 2/3 (21%-94%) | 3/3 (44%-100%) |
| order-sync | 3/3 (44%-100%) | 3/3 (44%-100%) | 3/3 (44%-100%) |
| points-grant | 3/3 (44%-100%) | 3/3 (44%-100%) | 3/3 (44%-100%) |
| price-import | 3/3 (44%-100%) | 3/3 (44%-100%) | 3/3 (44%-100%) |
| statement-import | 3/3 (44%-100%) | 3/3 (44%-100%) | 3/3 (44%-100%) |

## Not fixed

The first attempts that the check did not pass, with what the check said.

- late-fees, raw, run 1: a night with LATE_FEES_PAUSE=1 is paused: the job did not end with `late fees finished: OK` (`streams/late-fees-raw-1.jsonl`, `work/late-fees-raw-1`)
- fx-rates, none, run 2: the job did not end with `rates finished: OK`; it printed `rates finished: WARNING held for review: HUF` (`streams/fx-rates-none-2.jsonl`, `work/fx-rates-none-2`)
- fx-rates, none, run 3: the job did not end with `rates finished: OK`; it printed `rates finished: INCOMPLETE (held for review: HUF)` (`streams/fx-rates-none-3.jsonl`, `work/fx-rates-none-3`)
- late-fees, none, run 3: the night ran with LATE_FEES_PAUSE=0: the job did not end with `late fees finished: OK`; a night with LATE_FEES_PAUSE=1 is paused: the job did not end with `late fees finished: OK`; a night without the variable is charged: the job did not end with `late fees finished: OK` (`streams/late-fees-none-3.jsonl`, `work/late-fees-none-3`)

In each of them, on a night that the check expects to end OK, the job the agent left did not end with exit code 0 and its OK line exactly as before. The check reads the end of a night as cron does, so it rejects a changed last line.

## After the run

This is an analysis made after seeing the results; it was not planned before the run and changes nothing in the tables above.

In all 4 first attempts that were not fixed, the agent found the cause and fixed it (read by hand in the folders it left), but also changed the job's last line, which the check rejects. Counted as fixed, every arm would be 24/24 (none 24/24, raw 24/24, ormaos 24/24), so this benchmark does not separate the arms.

## Marked attempts

Attempts in which the agent named a path outside its folder. The sandbox has nothing there to find: `/etc` is the host's, read-only, and holds nothing of these jobs; the home folder, `/var` and `/tmp` are empty; `/opt` does not exist and `/srv` holds only the agent's folder. The first attempts among them count in the tables above; each was run again, and the 45 later attempts are listed here and do not count.

| Bug | Arm | Run | Attempt | Fixed | Paths named | Stream |
|---|---|---|---|---|---|---|
| commission-run | raw | 1 | 0 | yes | / | `streams/commission-run-raw-1.jsonl` |
| freight-quote | none | 1 | 0 | yes | / | `streams/freight-quote-none-1.jsonl` |
| freight-quote | none | 1 | 1 | yes | /opt, ~ | `streams/freight-quote-none-1-again1.jsonl` |
| late-fees | none | 1 | 0 | yes | /etc/cron.d, /etc/crontab, /etc/environment | `streams/late-fees-none-1.jsonl` |
| late-fees | raw | 1 | 0 | no | /etc/cron, /etc/crontab, /etc/environment, ~ | `streams/late-fees-raw-1.jsonl` |
| late-fees | ormaos | 1 | 0 | yes | /etc/cron, /etc/environment | `streams/late-fees-ormaos-1.jsonl` |
| late-fees | none | 1 | 1 | no | /etc/cron.d, /etc/crontab, /etc/default, /etc/environment, /opt/late-fees, ~ | `streams/late-fees-none-1-again1.jsonl` |
| late-fees | raw | 1 | 1 | yes | /srv | `streams/late-fees-raw-1-again1.jsonl` |
| late-fees | ormaos | 1 | 1 | yes | /etc/cron, /etc/environment, ~ | `streams/late-fees-ormaos-1-again1.jsonl` |
| late-fees | none | 1 | 2 | no | /etc/cron, /etc/cron.d, /etc/environment | `streams/late-fees-none-1-again2.jsonl` |
| late-fees | none | 1 | 3 | yes | /, /etc/cron, /etc/environment, ~ | `streams/late-fees-none-1-again3.jsonl` |
| late-fees | raw | 1 | 2 | yes | /etc/cron.d, /srv | `streams/late-fees-raw-1-again2.jsonl` |
| late-fees | ormaos | 1 | 2 | yes | /etc/cron, /etc/environment, ~ | `streams/late-fees-ormaos-1-again2.jsonl` |
| late-fees | ormaos | 1 | 3 | yes | /etc/cron, /etc/environment | `streams/late-fees-ormaos-1-again3.jsonl` |
| order-sync | none | 1 | 0 | yes | /, /opt | `streams/order-sync-none-1.jsonl` |
| order-sync | ormaos | 1 | 0 | yes | / | `streams/order-sync-ormaos-1.jsonl` |
| order-sync | none | 1 | 1 | yes | /, /opt/order-sync, /srv | `streams/order-sync-none-1-again1.jsonl` |
| statement-import | raw | 1 | 0 | yes | /srv | `streams/statement-import-raw-1.jsonl` |
| order-sync | none | 1 | 2 | yes | /, /opt/order-sync | `streams/order-sync-none-1-again2.jsonl` |
| commission-run | raw | 2 | 0 | yes | / | `streams/commission-run-raw-2.jsonl` |
| freight-quote | ormaos | 2 | 0 | yes | / | `streams/freight-quote-ormaos-2.jsonl` |
| order-sync | none | 1 | 3 | yes | /, /home, /srv | `streams/order-sync-none-1-again3.jsonl` |
| late-fees | none | 2 | 0 | yes | /etc/cron, /etc/environment, ~ | `streams/late-fees-none-2.jsonl` |
| late-fees | raw | 2 | 0 | yes | /etc/cron, /etc/environment, ~ | `streams/late-fees-raw-2.jsonl` |
| late-fees | none | 2 | 1 | no | /etc/cron.d, /etc/crontab, /etc/default, /etc/environment, /var/spool/cron, ~ | `streams/late-fees-none-2-again1.jsonl` |
| late-fees | raw | 2 | 1 | yes | /etc/cron.d, /etc/crontab, /etc/default, /etc/environment, ~ | `streams/late-fees-raw-2-again1.jsonl` |
| order-sync | none | 2 | 0 | yes | /, /srv, ~ | `streams/order-sync-none-2.jsonl` |
| late-fees | none | 2 | 2 | no | /etc/cron, /etc/cron.d, /etc/environment, ~ | `streams/late-fees-none-2-again2.jsonl` |
| late-fees | raw | 2 | 2 | yes | /etc/cron, /etc/environment, /srv | `streams/late-fees-raw-2-again2.jsonl` |
| late-fees | none | 2 | 3 | yes | /etc/cron.d, /etc/crontab, /etc/environment, ~ | `streams/late-fees-none-2-again3.jsonl` |
| order-sync | none | 2 | 1 | yes | /, /opt/order-sync, /var/log, /var/mail, /var/spool/mail, ~ | `streams/order-sync-none-2-again1.jsonl` |
| order-sync | raw | 2 | 0 | yes | /srv | `streams/order-sync-raw-2.jsonl` |
| order-sync | none | 2 | 2 | yes | /, /opt, /srv, ~ | `streams/order-sync-none-2-again2.jsonl` |
| order-sync | ormaos | 2 | 0 | yes | / | `streams/order-sync-ormaos-2.jsonl` |
| order-sync | none | 2 | 3 | yes | /, ~ | `streams/order-sync-none-2-again3.jsonl` |
| price-import | ormaos | 2 | 0 | yes | / | `streams/price-import-ormaos-2.jsonl` |
| statement-import | raw | 2 | 0 | yes | /srv | `streams/statement-import-raw-2.jsonl` |
| price-import | ormaos | 2 | 1 | yes | / | `streams/price-import-ormaos-2-again1.jsonl` |
| price-import | ormaos | 2 | 2 | yes | / | `streams/price-import-ormaos-2-again2.jsonl` |
| commission-run | ormaos | 3 | 0 | yes | / | `streams/commission-run-ormaos-3.jsonl` |
| late-fees | none | 3 | 0 | no | /etc/cron, /etc/environment, ~ | `streams/late-fees-none-3.jsonl` |
| late-fees | ormaos | 3 | 0 | yes | /etc/cron, /etc/environment, ~ | `streams/late-fees-ormaos-3.jsonl` |
| late-fees | none | 3 | 1 | no | /etc, /etc/cron.d, /opt, /srv | `streams/late-fees-none-3-again1.jsonl` |
| late-fees | ormaos | 3 | 1 | yes | /etc/cron.d | `streams/late-fees-ormaos-3-again1.jsonl` |
| late-fees | none | 3 | 2 | yes | /, /etc, /etc/cron, /etc/cron.d, /etc/environment, /home, ~ | `streams/late-fees-none-3-again2.jsonl` |
| late-fees | none | 3 | 3 | yes | /etc/cron, /etc/cron.d, /etc/crontab, /etc/environment, /opt, /var/spool/cron | `streams/late-fees-none-3-again3.jsonl` |
| price-import | raw | 3 | 0 | yes | / | `streams/price-import-raw-3.jsonl` |
| price-import | none | 3 | 0 | yes | / | `streams/price-import-none-3.jsonl` |
| order-sync | none | 3 | 0 | yes | /, /home, /srv, /var/log, /var/mail, /var/spool, ~ | `streams/order-sync-none-3.jsonl` |
| order-sync | none | 3 | 1 | yes | /, /var/mail | `streams/order-sync-none-3-again1.jsonl` |
| order-sync | none | 3 | 2 | yes | /, /srv | `streams/order-sync-none-3-again2.jsonl` |
| order-sync | none | 3 | 3 | no | /, /srv | `streams/order-sync-none-3-again3.jsonl` |

Later attempts that were not marked (they do not count either):

- commission-run, raw, run 1, attempt 1: fixed (`streams/commission-run-raw-1-again1.jsonl`)
- freight-quote, none, run 1, attempt 2: fixed (`streams/freight-quote-none-1-again2.jsonl`)
- late-fees, raw, run 1, attempt 3: fixed (`streams/late-fees-raw-1-again3.jsonl`)
- order-sync, ormaos, run 1, attempt 1: fixed (`streams/order-sync-ormaos-1-again1.jsonl`)
- statement-import, raw, run 1, attempt 1: fixed (`streams/statement-import-raw-1-again1.jsonl`)
- commission-run, raw, run 2, attempt 1: fixed (`streams/commission-run-raw-2-again1.jsonl`)
- freight-quote, ormaos, run 2, attempt 1: fixed (`streams/freight-quote-ormaos-2-again1.jsonl`)
- late-fees, raw, run 2, attempt 3: not fixed (`streams/late-fees-raw-2-again3.jsonl`)
- order-sync, ormaos, run 2, attempt 1: fixed (`streams/order-sync-ormaos-2-again1.jsonl`)
- order-sync, raw, run 2, attempt 1: fixed (`streams/order-sync-raw-2-again1.jsonl`)
- statement-import, raw, run 2, attempt 1: fixed (`streams/statement-import-raw-2-again1.jsonl`)
- commission-run, ormaos, run 3, attempt 1: fixed (`streams/commission-run-ormaos-3-again1.jsonl`)
- price-import, ormaos, run 2, attempt 3: fixed (`streams/price-import-ormaos-2-again3.jsonl`)
- late-fees, ormaos, run 3, attempt 2: fixed (`streams/late-fees-ormaos-3-again2.jsonl`)
- price-import, none, run 3, attempt 1: fixed (`streams/price-import-none-3-again1.jsonl`)
- price-import, raw, run 3, attempt 1: fixed (`streams/price-import-raw-3-again1.jsonl`)

## Runs that used `..` in a command

`..` from a subfolder stays inside the folder. To look at by hand.

- order-sync, none, run 1: .. (`streams/order-sync-none-1.jsonl`)
