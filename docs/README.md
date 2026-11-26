# The demo page

`index.html` is the whole page: static, no build step. `casts/` holds the terminal recordings it plays (asciinema, format v2). The page loads one third-party script, the asciinema player, from a pinned version on jsDelivr with an integrity hash, and nothing else.

It is published at <https://ormaos.com/demo>. `404.html` is what any other address below it answers.

## Looking at it locally

```bash
python3 -m http.server -d docs
```

Then open the address it prints. Opened straight from the file system (`docs/index.html`), the text is all there, but the recordings do not play: a browser does not let a page opened from a file read the file next to it. To play one in a terminal: `asciinema play docs/casts/human.cast`.

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
asciinema rec --cols 120 --rows 34 -c "/path/to/scenarios/casts/human.sh r1:c130" human.cast
```

The address after `human.sh` is the call that handled the exception: the one `ormaos exceptions r1:e1` prints after "handled at". It is `r1:c130` on Python 3.14 and not the same on every Python version.

`without.cast` and `with.cast`, one agent run each on the morning after a night run (needs `bwrap` and a signed-in `claude` command line):

```bash
python3 scenarios/morning_after.py /tmp/morning-plain
python3 scenarios/morning_after.py /tmp/morning-recorded --record
asciinema rec --cols 120 --rows 34 -c "scenarios/casts/agent.sh /tmp/morning-plain without /tmp/without.jsonl" docs/casts/without.cast
asciinema rec --cols 120 --rows 34 -c "scenarios/casts/agent.sh /tmp/morning-recorded with /tmp/with.jsonl" docs/casts/with.cast
```

`agent.sh` starts `claude -p` with only the prompt, inside `isolated.sh` (bubblewrap: the system read-only, the agent's own folder, nothing else of the machine). `render.py` prints each step of the agent's stream as it arrives; the whole stream is kept in the `.jsonl` file, outside the agent's folder. Before a recording is committed, read the stream for anything the agent reached outside its folder, and read the cast for anything that should not be public.

To show a recording on the page, add an element with its file name where it belongs in `index.html`:

```html
<div class="cast" data-cast="casts/without.cast"></div>
```

Before it plays, each recording shows the session two seconds in: the first command, typed, and nothing else. For a recording whose first command takes longer to appear, add `data-poster="npt:0:05"` (minutes:seconds) to the element.
