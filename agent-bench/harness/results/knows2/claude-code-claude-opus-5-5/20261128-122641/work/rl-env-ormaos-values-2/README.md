# rl-env: a grid world

A reinforcement-learning environment in pure Python, and a loop that runs episodes of it.

- `env.py`: `GridEnv`, a 6 x 6 grid with walls. A courier starts at the depot `(0, 0)` and walks to a customer at `(5, 5)`. `reset()` gives the first observation; `step(action)` gives `(observation, reward, done)`. The reward is 10 at the customer, and otherwise a cost of 0.1 for every cell still to walk. An episode ends at the customer or after 30 steps.
- `run.py`: 20 episodes with a seeded policy that walks towards the customer and explores 30% of the time.

## Run it

```bash
python run.py
```

It prints one line:

```
20 episodes, mean return -10.55
```

Standard library only.
