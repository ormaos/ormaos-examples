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
        return "down" if goal[1] > position[1] else "up"
    return "right" if goal[0] > position[0] else "left"


def ended_at_goal(returns, total):
    returns.append(total)


def ended_at_limit(returns, total):
    returns.append(total)


def run_episode(env, rng, returns):
    position = env.reset()
    total, done = 0.0, False
    while not done:
        position, reward, done = env.step(choose(rng, position, env.goal))
        total += reward
    if position == env.goal:
        ended_at_goal(returns, total)
    else:
        ended_at_limit(returns, total)


def main():
    rng = random.Random(3)
    env = GridEnv()
    returns = []
    for _ in range(EPISODES):
        run_episode(env, rng, returns)
    print(f"{len(returns)} episodes, mean return {sum(returns) / len(returns):.2f}")


if __name__ == "__main__":
    main()
