from queue import Queue
import numpy as np
import numpy.typing as npt

from board import Board, Entity, toroidal_distance_2, neighbors

Point = tuple[int, int]
Vector = Point # Just going to use this to make sure I know which are points and which are movement vectors
AntMove = tuple[tuple[int, int], tuple[int, int]]


def valid_neighbors(
    row: int, col: int, walls: npt.NDArray[np.int_]
) -> list[Vector]:
    if len(walls.shape) != 2:
        return []
    return [n for n in neighbors((row, col), walls.shape) if not walls[n]]

class Player:
    """
    Your player must match this protocol. (It must have each of these functions with the same signatures)
    The constructor provides your player object with the information that won't change during the game.
    You must have a name property that returns a string

    Your move function takes as input the things you can see as a set of tuples containing a coordinate and an Enum
    telling you what kind of thing is at that location. This will always include all of your ants and hills. Your ants
    and hills can see enemy ants, enemy hills, and food in a certain radius of them.

    You will push all of your moves into the provided move_queue in the form (start_loc, end_loc) where both locations
    are given as tuple[int, int]. When you run out of time for the turn, the function will be terminated and whatever moves
    you managed to push in time will be executed.
    """

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

    @property
    def name(self) -> str:
        return "Jack And Niko's Bot"

    def move_ants(
        self,
        vision: set[tuple[tuple[int, int], Entity]],
        stored_food: int, 
    ) -> set[AntMove]:

        bot_ants: set[Point] = set()
        bot_ant_legal_moves: set[tuple[Point, list[Vector]]] = set()
        bot_hills: set[Point] = set()
        visible_food: set[Point] = set()
        visible_enemy_ants: set[Point] = set()
        enemy_hill: set[Point] = set()


        for coord, kind in vision:  # get all locations for each type
            if kind == Entity.FRIENDLY_ANT:
                bot_ants.add(coord)
                bot_ant_legal_moves.add((coord, valid_neighbors(coord[0], coord[1], self.walls)))
            elif kind == Entity.ENEMY_ANT:
                visible_enemy_ants.add(coord)
            elif kind == Entity.FOOD:
                visible_food.add(coord)
            elif kind == Entity.FRIENDLY_HILL:
                bot_hills.add(coord)
            elif kind == Entity.ENEMY_HILL:
                enemy_hill.add(coord)

        

        return set()
