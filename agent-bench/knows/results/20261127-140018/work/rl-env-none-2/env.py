"""A grid world: a courier walks from the depot to a customer, around walls."""

MOVES = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
WALLS = {(2, 0), (2, 1), (2, 2), (4, 4), (1, 4)}


class GridEnv:
    """Observation: the position. Reward: 10 at the customer, else a small
    cost that grows with the distance still to walk."""

    def __init__(self, size=6, start=(0, 0), goal=(5, 5), limit=30):
        self.size = size
        self.start = start
        self.goal = goal
        self.limit = limit
        self.position = start
        self.steps = 0
        self.bumps = 0

    def reset(self):
        self.position = self.start
        self.steps = 0
        return self.position

    def step(self, action):
        reward = self._reward()
        self._move(action)
        self.steps += 1
        done = self.position == self.goal or self.steps >= self.limit
        return self.position, reward, done

    def _reward(self):
        if self.position == self.goal:
            return self._arrival_bonus()
        return -0.1 * self._distance()

    def _arrival_bonus(self):
        return 10.0

    def _distance(self):
        return abs(self.goal[0] - self.position[0]) + abs(self.goal[1] - self.position[1])

    def _move(self, action):
        dx, dy = MOVES[action]
        x, y = self.position[0] + dx, self.position[1] + dy
        if not (0 <= x < self.size and 0 <= y < self.size) or (x, y) in WALLS:
            self._bump()
            return
        self.position = (x, y)

    def _bump(self):
        self.bumps += 1
