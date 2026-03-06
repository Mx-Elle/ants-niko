from copy import deepcopy
from enum import Enum
import pickle
from queue import Queue
from time import monotonic
import numpy as np
import numpy.typing as npt

from board import Board, Entity, toroidal_distance_2, neighbors

Point = tuple[int, int]
AntMove = tuple[tuple[int, int], tuple[int, int]]


class Bot:

    def __init__(
        self,
        walls: npt.NDArray[np.int_],
        harvest_radius: int,
        vision_radius: int,
        battle_radius: int,
        max_turns: int,
        time_per_turn: float,
    ) -> None:

        self.walls = walls
        self.harvest_radius = harvest_radius
        self.vision_radius = vision_radius
        self.battle_radius = battle_radius
        self.max_turns = max_turns
        self.time_per_turn = time_per_turn

        with open('final_nn_weights.pkl', 'rb') as file:
            genome = pickle.load(file)
        file.close()

        genome = genome[0]

        self.filter_one = genome[0]
        self.bias_one = genome[1]
        self.filter_two = genome[2]
        self.bias_two = genome[3]
        self.flat_filter = genome[4]
        self.flat_bias = genome[5]

    @property
    def name(self) -> str:
        return "Jack And Niko's Bot"

    def move_ants(
        self,
        vision: set[tuple[tuple[int, int], Entity]],
        stored_food: int,
    ) -> set[AntMove]:
        # learned a lot from https://medium.com/@prxdyu/simple-neural-network-in-python-from-scratch-2814443a3050
        # only used as pseudocode and understanding, not direct copying

        bot_ants: set[Point] = set()
        ant_moves: set[AntMove] = set()

        full_map = np.zeros((self.walls.shape[0], self.walls.shape[1], 6))
        full_map[self.walls == 1][0] = 1

        # making it a 3d array with following idxs of the 3rd dimension

        # 0: wall
        # 1: friendly
        # 2: enemy
        # 3: food
        # 4: friendly hill
        # 5: enemy hill

        # this makes it all zeros or ones, which make the filters in the convolution possible

        for coord, kind in vision:  # get all locations for each type

            if kind == Entity.FRIENDLY_ANT:
                full_map[coord][1] = 1
                bot_ants.add(coord)

            elif kind == Entity.ENEMY_ANT:
                full_map[coord][2] = 1

            elif kind == Entity.FOOD:
                full_map[coord][3] = 1

            elif kind == Entity.FRIENDLY_HILL:
                full_map[coord][4] = 1

            elif kind == Entity.ENEMY_HILL:
                full_map[coord][5] = 1

        # decide what ants go where

        # Convolute full map

        # 2 Convolutions of 3x3 shapes
        # Convolutions find patterns
        # First convolution has 8 filters

        padded_map = np.pad(full_map, ((3, 3), (3, 3), (0, 0)), mode="wrap")

        convolute_one = np.zeros((padded_map.shape[0] - 2, padded_map.shape[1] - 2, 8))


        for r in range(0, padded_map.shape[0] - 2):
            for c in range(0, padded_map.shape[1] - 2):
                patch_one = padded_map[r : r + 3, c : c + 3]

                multiplied_one = patch_one * self.filter_one

                summed_one = np.sum(multiplied_one, axis=(1,2,3))

                summed_one += self.bias_one

                # ReLU
                convolute_one[r, c] = np.maximum(0, summed_one)

        # Second convolution is 16 filters

        convolute_two = np.zeros((9, 9, 16))

        for r in range(0, convolute_two.shape[0] - 2):
            for c in range(0, convolute_two.shape[1] - 2):
                patch_two = convolute_one[r : r + 3, c : c + 3]

                multiplied_two = patch_two * self.filter_two

                summed_two = np.sum(multiplied_two, axis=(1,2,3))

                summed_two += self.bias_two
                convolute_two[r, c] = np.maximum(0, summed_two)
        
        # use convolutions to create 13x13 space around each ant, and use it to decide which direction is best

        window = np.arange(-6, 7)
        Height = convolute_two.shape[0]
        Width = convolute_two.shape[1]

        for ant_loc in bot_ants:
            row_idxs = (ant_loc[0] - 2 + window) % Height
            column_idxs = (ant_loc[1] - 2 + window) % Width

            ant_sight = convolute_two[row_idxs[:, None], column_idxs]

            # Flatten
            flat = ant_sight.flatten()

            final_set = (flat @ self.flat_filter) + self.flat_bias

            move_vector = {0: (-1, 0), 1: (1, 0), 2: (0, -1), 3: (0, 1), 4: (0, 0)}

            move = move_vector[max([0, 1, 2, 3, 4], key=lambda x: final_set[x])]

            ant_moves.add((ant_loc, (ant_loc[0] + move[0], ant_loc[1] + move[1])))


        return ant_moves

