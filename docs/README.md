# The demo page

`index.html` is the whole page: static, no build step. `casts/` holds the terminal recordings it plays (asciinema, format v2). Under each player, closed until asked for, is the whole text of its recording, and every block has a copy button. [`check_docs.py`](../.github/scripts/check_docs.py) fails when that text is not the recording, or when a number of the results table is not in the report. The page loads one third-party script, the asciinema player, from a pinned version on jsDelivr with an integrity hash, and nothing else.

The section "Seven kinds of program" shows, for each folder of [`use-cases/`](../use-cases), the `demo.txt` its `scenario.py --update` wrote: the check compares each block with that file.

It is published at <https://ormaos.com/demo>. `404.html` is what any other address below it answers.

## The benchmark pages

`benchmarks/` holds the benchmark pages, meant for `https://ormaos.com/benchmarks/`: an index, one page per benchmark, each page also as Markdown (`index.html.md`), and `llms.txt`. They are written by [`site/benchmarks/build.py`](../site/benchmarks/build.py) from the results files of [`agent-bench/`](../agent-bench) and from [`site/benchmarks/overhead/RESULTS.md`](../site/benchmarks/overhead/RESULTS.md), a copy of the overhead results of ormaos-python; nothing in `benchmarks/` is edited by hand. Run the build again after a change to a results file, to the build, or to the style, header or footer of `index.html`, which the pages take from it:

```bash
python3 site/benchmarks/build.py
```

CI runs it with `--check`, which fails when `benchmarks/` is not what a fresh build writes. `--overhead ../ormaos-python` first takes `bench/RESULTS.md` again from a checkout of ormaos-python, with the commit that last changed it. The build names the commit that added each results file, so it needs the full git history.

The pages link to each other with absolute paths under `/benchmarks/`. On this Pages project they are at `/benchmarks/`; on ormaos.com that path needs a route to the project, as `/demo` has.

## Looking at it locally

```bash
python3 -m http.server -d docs
```

Then open the address it prints, and `/benchmarks/` below it for the benchmark pages. Opened straight from the file system (`docs/index.html`), the text is all there, but the recordings do not play: a browser does not let a page opened from a file read the file next to it. To play one in a terminal: `asciinema play docs/casts/human.cast`.

## How it is deployed

The site is a Cloudflare Pages project named `ormaos-demo`, connected to this repository:

- production branch `main`, no build command, output directory `docs`: what is served is exactly the content of this folder at the commit that was deployed;
- only `main` is deployed; other branches and pull requests are not;
- every push to `main` starts a deployment: the workflow [`deploy-demo.yml`](../.github/workflows/deploy-demo.yml) calls the project's deploy hook, whose address is the repository secret `DEMO_DEPLOY_HOOK`. It is live in under a minute.

Visitors read it at `https://ormaos.com/demo/`. A small Worker, `ormaos-demo-proxy`, on the route `ormaos.com/demo*`, passes each request to the Pages project; its source is in the site's repository ([`demo-proxy/`](https://github.com/ormaos/ormaos-site/tree/main/demo-proxy)). Every path in `index.html` is relative, so the page works below `/demo/` as it does at the root of a local server. `https://demo.ormaos.com` redirects to `https://ormaos.com/demo/` (a redirect rule in the `ormaos.com` zone).

**To check what is served** after a push:

```bash
curl -s https://ormaos.com/demo/ | sha256sum; sha256sum docs/index.html
```

The two sums are the same. The deployments and their logs are in the Cloudflare dashboard, Workers & Pages, `ormaos-demo`; "Create deployment" there, branch `main`, starts one by hand.

## The recordings

All are real runs, recorded with `asciinema rec` and never edited. The scripts are in [`scenarios/casts/`](../scenarios/casts/).

`human.cast`, in a fresh copy of `order-sync` outside the repository:

```bash
cp -r order-sync /tmp/order-sync && cd /tmp/order-sync
PIP_DISABLE_PIP_VERSION_CHECK=1 asciinema rec --cols 80 --rows 30 -c "/path/to/scenarios/casts/human.sh r1:c130" human.cast
```

The variable keeps pip from ending its output with a notice about a newer pip.

The address after `human.sh` is the call that handled the exception: the one `ormaos exceptions r1:e1` prints after "handled at". It is `r1:c130` on Python 3.14 and not the same on every Python version.

`without.cast` and `with.cast`, one agent run each on the morning after a night run (needs `bwrap` and a signed-in `claude` command line):

```bash
python3 scenarios/morning_after.py /tmp/morning-plain
python3 scenarios/morning_after.py /tmp/morning-recorded --record
asciinema rec --cols 100 --rows 34 -c "scenarios/casts/agent.sh /tmp/morning-plain without /tmp/without.jsonl" docs/casts/without.cast
asciinema rec --cols 100 --rows 34 -c "scenarios/casts/agent.sh /tmp/morning-recorded with /tmp/with.jsonl" docs/casts/with.cast
```

`agent.sh` starts `claude -p` with only the prompt, inside `isolated.sh` (bubblewrap: the system read-only, the agent's own folder, nothing else of the machine). `render.py` prints each step of the agent's stream as it arrives; the whole stream is kept in the `.jsonl` file, outside the agent's folder. Before a recording is committed, read the stream for anything the agent reached outside its folder, and read the cast for anything that should not be public.

`diff.cast`, in a folder built by the second scenario, with both nights recorded:

```bash
python3 scenarios/two_nights.py /tmp/freight-quote-recorded --record
cd /tmp/freight-quote-recorded
asciinema rec --cols 80 --rows 30 -c /path/to/scenarios/casts/diff.sh diff.cast
```

The short sessions are 80 columns wide, so that the font of the player is large; the agent runs are 100.

The recording the home page of ormaos.com plays, `casts/home.cast` in the site's repository, is made the same way, in a fresh copy of `order-sync` with Ormaos installed in `.venv` and `./reset.sh` run:

```bash
asciinema rec --cols 80 --rows 24 -c /path/to/scenarios/casts/home.sh home.cast
```

A recording is shown in a terminal window: a bar with its title, then the element the player fills, then the text of the same session.

```html
<div class="term player">
<div class="code-bar"><span class="code-label">order-sync</span></div>
<div class="cast" data-cast="casts/human.cast" data-poster="npt:0:24" data-rows="30"></div>
</div>
```

Before it plays, a recording shows its last screen: `data-poster` is the first whole second after its end in playback time, where every pause is cut to 1.5 seconds. `data-rows` is the number of rows it was recorded in. It starts by itself the first time it is on screen, unless the reader asked for less motion (`prefers-reduced-motion`); pressing play starts it from the beginning.
