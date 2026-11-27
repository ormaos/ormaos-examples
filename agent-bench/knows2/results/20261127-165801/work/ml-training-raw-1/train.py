"""Train a small regression model on CPU: delivery time from four features."""

import random
from pathlib import Path

import torch
from torch import nn

HERE = Path(__file__).parent
BATCH = 8


def make_data(rows=320, seed=5):
    """Distance, parcels, hour of the day and a weekend flag; minutes to deliver."""
    rng = random.Random(seed)
    features, minutes = [], []
    for _ in range(rows):
        distance = rng.uniform(1, 30)
        parcels = rng.randint(1, 12)
        hour = rng.randint(8, 20)
        weekend = 1.0 if rng.random() < 0.3 else 0.0
        features.append([distance, parcels, hour, weekend])
        minutes.append(4 * distance + 2 * parcels + 6 * weekend + rng.gauss(0, 3))
    return torch.tensor(features), torch.tensor(minutes)


def batches(features, minutes):
    for start in range(0, len(features), BATCH):
        yield features[start : start + BATCH], minutes[start : start + BATCH]


def standardize(batch):
    return (batch - batch.mean(dim=0)) / batch.std(dim=0)


def predict(model, batch):
    return model(batch).squeeze(1)


def loss_of(predicted, minutes):
    return nn.functional.mse_loss(predicted, minutes)


def apply_update(optimizer, loss):
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()


def train_step(model, optimizer, batch, minutes):
    loss = loss_of(predict(model, standardize(batch)), minutes)
    if not torch.isfinite(loss):
        return None
    apply_update(optimizer, loss)
    return loss.item()


def save_checkpoint(model, path):
    torch.save(model.state_dict(), path)


def main():
    torch.manual_seed(0)
    features, minutes = make_data()
    model = nn.Sequential(nn.Linear(4, 16), nn.ReLU(), nn.Linear(16, 1))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.05)
    steps, last = 0, None
    for batch, target in batches(features, minutes):
        loss = train_step(model, optimizer, batch, target)
        steps += 1
        if loss is not None:
            last = loss
    save_checkpoint(model, HERE / "model.pt")
    print(f"trained {steps} steps, last loss {last:.1f}, checkpoint model.pt")


if __name__ == "__main__":
    main()
