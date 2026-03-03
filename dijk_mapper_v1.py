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


class DijkBot:

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

        self.previous_ants: set[Point]
        self.dead_ants: set[Point]
        self.run_count = 1
        self.d_map: npt.NDArray[np.float32] = self.walls.copy().astype(np.float32)
        self.walls_init = False

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
        Food = 1,
        Defend = 2,
        Attack = 3,
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

        return


    def kill_ants(self, curr_ants: set[Point]) -> None:
        """updates dead_ants set with ants that just died"""
        self.dead_ants = self.previous_ants - curr_ants
        return

    def create_dijk_map(self) -> None:
        if not self.walls_init:
            # make walls inf on first run
            for wall in np.nonzero(self.d_map):
                self.d_map[wall] = np.inf
            self.walls_init = True

        # make enemy ant death radius inf
        death_radius: set[Point] = cells_within_radius(
            self.enemy_ants,
            self.battle_radius,
            self.walls
        )
        for death in death_radius:
            self.d_map[death] = np.inf



    def move_ants(
        self,
        vision: set[tuple[Point, Entity]],
        stored_food: int,
    ) -> set[AntMove]:
        start = monotonic()
        out = set()

        self.process_vision(vision)

        claimed_destinations: set[Point] = self.my_hills
        claimed_ants: set[Point] = set()

        food_and_ant: dict[Point, list[tuple[float, Point]]]= dict()
        food_ant_q: list[tuple] = list()

        for food in self.foods:
            food_and_ant[food] = list()
            for ant in self.my_ants:
                heapq.heappush(food_and_ant[food], (
                    dist(ant, food, self.walls),
                    ant
                ))
            dis, ant = heapq.heappop(food_and_ant[food])
            heapq.heappush(food_ant_q, (
                dis,
                food,
                ant
            ))

        while food_ant_q:
            dis, food, ant = heapq.heappop(food_ant_q)
            if ant in claimed_ants:
                if food_and_ant[food]:
                    dis, ant2 = heapq.heappop(food_and_ant[food])
                    heapq.heappush(food_ant_q, (
                        dis,
                        food,
                        ant2
                    ))
            else:
                dest = move_towards_dest(ant, food, self.walls)
                claimed_ants.add(ant)
                claimed_destinations.add(dest)
                self.previous_ants.add(dest)
                out.add((ant, dest))


        unc_ant_count = 0
        for ant in (self.my_ants - claimed_ants):
            unc_ant_count += 1
            valid_dests = {
                v
                for v in valid_neighbors(*ant, self.walls)
                if v not in claimed_destinations
            }

            if not valid_dests:
                # if no possible moves stay still
                claimed_destinations.add(ant)
                continue

            dest = random.choice(list(valid_dests))
            claimed_destinations.add(dest)
            self.previous_ants.add(dest)
            out.add((ant, dest))


        print(f"v2 unclaimed ants: {unc_ant_count}")
        end = monotonic()
        print(f"v2 move time {round(((end - start) / self.time_per_turn) * 100, 3)}%")
        return out
