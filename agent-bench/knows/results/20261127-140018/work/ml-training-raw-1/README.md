# ml-training: a small training loop

A PyTorch model, trained on CPU, that predicts the minutes a delivery takes from four features: distance, number of parcels, hour of the day and a weekend flag. The data is made by the script, the same every time. Each batch of 8 rows is standardized, the model takes one Adam step per batch, and a batch whose loss is not a finite number is left out. The weights are saved to `model.pt`.

## Run it

```bash
pip install -r requirements.txt     # the CPU build of torch is enough
python train.py
```

It prints one line:

```
trained 40 steps, last loss 379.2, checkpoint model.pt
```

The loss can differ in the last digits from one build of torch to another.
