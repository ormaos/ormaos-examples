# ai-app: ticket summaries

An app that sends each support ticket of `tickets.json` to a model API and keeps a one-sentence summary of it in `summaries.json`.

The model API here is `model_server.py`, a stand-in that runs on `127.0.0.1` on a free port and is started by the app, so nothing leaves the machine and no key is needed. It has two models, `small-1` and `large-1`, behind `POST /v1/models/<model>/generate`.

## Run it

```bash
python app.py
```

It prints one line:

```
8 tickets summarized, summaries.json written
```

Standard library only.
