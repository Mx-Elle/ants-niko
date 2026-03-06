from enum import Enum

from board import Entity, neighbors, cells_within_distance, toroidal_distance_2
import random
import numpy as np
import numpy.typing as npt
import heapq
from time import monotonic


Point = tuple[int, int]
AntPosition = Point
AntDestination = Point

AntMove = tuple[AntPosition, AntDestination]

# are any vectors ever used?
# Vector = tuple[int, int]
# # vector type for differentiating between points and vectors


def valid_neighbors(
    row: int, col: int, walls: npt.NDArray[np.int_]
) -> list[Point]:
    """
    empty spaces around a cell

    :return: neighbors without walls
    :rtype: list[Point]
    """
    return [n for n in neighbors((row, col), walls.shape) if not walls[n]]

def cells_within_radius(
    cells: set[Point] | Point, radius: int, walls: npt.NDArray[np.int_]
) -> set[Point]:
    """
    returns all cells within a certain radius of a cell\n
    or all cells with a certain radius of each cell in a set of cells

    :return: set of cells within radius of given cell or cells
    :rtype: set[Point]
    """
    result: set[Point] = set()

    if type(cells) == set:
        for cell in cells:
            result = result | cells_within_distance(radius, cell, walls.shape)
    elif type(cells) == Point:
        # could be acheived with else rather than elif
        # however, a pesky type warning appears
        result = cells_within_distance(radius, cells, walls.shape)
    return result

def dist(a: Point, b: Point, walls: npt.NDArray[np.int_]) -> float:
    """wrapper for board dist"""
    return toroidal_distance_2(a, b, walls.shape)

def move_towards_dest(
    a: Point, b: Point, walls: npt.NDArray[np.int_]
) -> Point:
    neighbors = valid_neighbors(a[0], a[1], walls)
    q: list[tuple] = list()
    for n in neighbors:
        heapq.heappush(q, (dist(n, b, walls), n))
    return heapq.heappop(q)[1]


class DijkBot1:

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
        self.collect_radius = harvest_radius
        self.vision_radius = vision_radius
        self.battle_radius = battle_radius
        self.max_turns = max_turns
        self.time_per_turn = time_per_turn

        self.previous_ants: set[Point] = set()
        # self.dead_ants: set[Point]
        self.d_map: npt.NDArray[np.float32] = self.walls.copy().astype(np.float32)
        self.walls_coords: set[Point] = set()
        self.floor_cells: set[Point] = set()
        self.map_init = False
        self.claimed_destinations = set()
        self.assigned_cells: set[Point] = set()
        self.permanent_cells: set[Point] = set()

        self.my_hills: set[Point]
        self.enemy_hills: set[Point]
        self.my_ants: set[Point]
        self.enemy_ants: set[Point]
        self.foods: set[Point]
        self.harvest_cells: set[Point]
        self.cells_in_view: set[Point]

    @property
    def name(self):
        return "dijkstra mapper 1"

    class Job(Enum):
        Food = 1
        Defend = 2
        Attack = 3
        DefendHill = 4

    def process_vision(
        self, vision: set[tuple[Point, Entity]]
    ) -> None:
        """
        process vision set and updates vision instance vars\n
        loops through vision set once
        """
        result: dict[Entity, set[Point]] = {
            Entity.FRIENDLY_HILL: set(),
            Entity.ENEMY_HILL: set(),
            Entity.FRIENDLY_ANT: set(),
            Entity.ENEMY_ANT: set(),
            Entity.FOOD: set()
        }

        for item in vision:
            coord, entity = item
            result[entity].add(coord)

        self.my_hills = result[Entity.FRIENDLY_HILL]
        self.enemy_hills = result[Entity.ENEMY_HILL]
        self.my_ants = result[Entity.FRIENDLY_ANT]
        self.enemy_ants = result[Entity.ENEMY_ANT]
        self.foods = result[Entity.FOOD]

        # kills ants during vision processing
        self.kill_ants(self.my_ants)

        self.harvest_cells = cells_within_radius(self.foods, self.collect_radius, self.walls)
        self.cells_in_view = cells_within_radius(self.my_ants, self.vision_radius, self.walls)

        self.create_dijk_map()

        return

    def kill_ants(self, curr_ants: set[Point]) -> None:
        """updates dead_ants set with ants that just died"""
        self.dead_ants = self.previous_ants - curr_ants
        self.previous_ants = curr_ants.copy()
        return

    def create_dijk_map(self) -> None:
        if not self.map_init:

            wall_list = list(zip(*np.nonzero(self.d_map)))
            not_wall_list = list(zip(*np.nonzero(self.d_map == 0)))

            for wall in wall_list:
                self.walls_coords.add(wall)

            for not_wall in not_wall_list:
                self.floor_cells.add(not_wall)


            self.permanent_cells = self.permanent_cells | self.walls_coords
            self.permanent_cells = self.permanent_cells | self.my_hills
            self.permanent_cells = self.permanent_cells | self.foods

            self.map_init = True

        self.d_map = self.walls.copy().astype(np.float32)
        goals = []

        if self.walls_coords:
            r, c = zip(*self.walls_coords)
            self.d_map[r, c] = np.inf

        if self.my_hills:
            r, c = zip(*self.my_hills)
            self.d_map[r, c] = np.inf

        for food in self.foods:
            self.d_map[food] = -50
            heapq.heappush(goals, (-50, food))

        # reset assigned cells after ants have moved
        self.assigned_cells = self.permanent_cells.copy()

        if self.floor_cells:
            r, c = zip(*self.floor_cells)
            self.d_map[r, c] = 999


        # make unseen cells low
        for cell in (self.floor_cells - self.cells_in_view):
            self.d_map[cell] = 5
            heapq.heappush(goals, (5, cell))

        # for cell in self.floor_cells - self.cells_in_view:
        #     self.d_map[cell] = 0
        #     # assigned_cells.add(cell) unsure about this?

        # make enemy ant death radius inf
        death_radius: set[Point] = cells_within_radius(
            self.enemy_ants,
            self.battle_radius,
            self.walls
        )
        
        # self.d_map[list(death_radius)] = np.inf
        # self.assigned_cells = self.assigned_cells | death_radius
        
        # for death in death_radius:
        #     self.d_map[death] = np.inf
        #     self.assigned_cells.add(death)

        # fill rest of map
        while goals:
            dist, cell = heapq.heappop(goals)
            if dist > self.d_map[cell]:
                continue

            neighbors = valid_neighbors(cell[0], cell[1], self.walls)
            for n in neighbors:
                new_cost = dist + 1
                if new_cost < self.d_map[n]:
                    self.d_map[n] = new_cost
                    heapq.heappush(goals, (new_cost, n))



    def dijk_move(self, current: Point) -> AntMove | None:
        n_vals: list[tuple] = list()
        tie = 1
        for n in valid_neighbors(current[0], current[1], self.walls):
            if n not in self.claimed_destinations:
                heapq.heappush(n_vals, (
                    self.d_map[n],
                    random.random(),
                    tie,
                    n
                ))
                tie += 1
        if n_vals:
            _, _, _, dest = heapq.heappop(n_vals)
            return (current, dest)

        else:
            return None




    def move_ants(
        self,
        vision: set[tuple[Point, Entity]],
        stored_food: int,
    ) -> set[AntMove]:
        start = monotonic()
        out: set[AntMove] = set()

        self.process_vision(vision)

        self.claimed_destinations: set[Point] = set()

        for ant in self.my_ants:
            move = self.dijk_move(ant)
            if move == None:
                self.claimed_destinations.add(ant)
            else:
                self.claimed_destinations.add(move[1])
                out.add(move)


        end = monotonic()
        # print(f"v2 move time {round(((end - start) / self.time_per_turn) * 100, 3)}%")
        return out
