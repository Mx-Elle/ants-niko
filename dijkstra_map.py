from collections import defaultdict
import heapq
from board import neighbors

import numpy as np


def create_map(array: np.ndarray):
    starts = np.argwhere(array < 0).tolist()
    frontier = []
    tie_break: int = 0
    g_scores = defaultdict(lambda: float("inf"))
    for start in starts:
        heapq.heappush(frontier, (array[tuple(start)], tie_break, tuple(start)))
        g_scores[tuple(start)] = array[tuple(start)]
    curr = frontier[0]

    while frontier != []:
        curr_g, _, curr = heapq.heappop(frontier)

        if curr_g > g_scores[curr]:
            continue

        for neighbor in neighbors(curr, array.shape):
            tie_break += 1
            new_cost = g_scores[curr] + 1

            if new_cost < g_scores[neighbor] and array[neighbor] != float('inf'):
                heapq.heappush(
                    frontier,
                    (new_cost, tie_break, neighbor),
                )
                g_scores[neighbor] = new_cost
                array[neighbor] = new_cost
    return array

array = np.zeros((5,5))
array[1::2, 3] = -1
array[0,0] = float('inf')
print(create_map(array))