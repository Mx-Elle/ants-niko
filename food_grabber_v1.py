from board import Entity, neighbors, cells_within_distance, toroidal_distance_2
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
) -> list[tuple[int, int]]:
    """
    empty spaces around a cell

    :return: neighbors without walls
    :rtype: list[tuple[int, int]]
    """
    return [n for n in neighbors((row, col), walls.shape) if not walls[n]]

def cells_within_radius(
    cells: set[Point] | Point, radius: int, map: npt.NDArray[np.int_]
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
            result = result | cells_within_distance(radius, cell, map.shape)
    elif type(cells) == Point:
        # could be acheived with else rather than elif
        # however, a pesky type warning appears
        result = cells_within_distance(radius, cells, map.shape)
    return result

class FoodBot:

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

        self.run_count = 1

    @property
    def name(self):
        return "food grabber"

    def process_vision(
        self, vision: set[tuple[Point, Entity]]
    ) -> dict[Entity, set[Point]]:
        """
        process vision set and return dict with coords for each entity\n
        loops through vision set once

        :return: dict with entity keys and coords as values
        :rtype: dict[Entity, set[Point]]
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
            # pesky type warning appears when
            # trying to do next three lines in one
            coords = result[entity]
            coords.add(coord)
            result[entity] = coords
        return result

    def move_ants(
        self,
        vision: set[tuple[Point, Entity]],
        stored_food: int,
    ) -> set[AntMove]:
        start = monotonic()
        out = set()

        # pv for processed vision
        pv = self.process_vision(vision)

        my_hills = pv[Entity.FRIENDLY_HILL]
        enemy_hills = pv[Entity.ENEMY_HILL]
        my_ants = pv[Entity.FRIENDLY_ANT]
        enemy_ants = pv[Entity.ENEMY_ANT]
        food = pv[Entity.FOOD]

        # food = {coord for coord, kind in vision if kind == Entity.FOOD}
        # my_ants = {coord for coord, kind in vision if kind == Entity.FRIENDLY_ANT}
        # my_hills = {coord for coord, kind in vision if kind == Entity.FRIENDLY_HILL}

        harvest_cells = cells_within_radius(food, self.collect_radius, self.walls)
        cells_in_view = cells_within_radius(my_ants, self.vision_radius, self.walls)

        claimed_destinations = my_hills

        for ant in my_ants:
            ant_start = monotonic()
            valid_dests = {
                v
                for v in valid_neighbors(*ant, self.walls)
                if v not in claimed_destinations
            }

            if not valid_dests:
                # if no possible moves stay still
                claimed_destinations.add(ant)
                continue


            # get food if adjacent
            moves_with_harvest = valid_dests & harvest_cells
            if moves_with_harvest:
                dest = moves_with_harvest.pop()
                claimed_destinations.add(dest)
                out.add((ant, dest))
                continue

            # go towards food if in vision
            ant_vision = cells_within_radius(ant, self.vision_radius, self.walls)
            unc_food_in_vision = (ant_vision & food) - claimed_destinations

            if unc_food_in_vision:
                foods: list[tuple[float, Point]] = []
                for loc in unc_food_in_vision:
                    heapq.heappush(foods, (toroidal_distance_2(ant, loc), loc))
                _, closest_food = heapq.heappop(foods)

                moves: list[tuple[float, Point]] = []
                for move in valid_dests:
                    heapq.heappush(moves, (toroidal_distance_2(move, closest_food), move))
                _, dest = heapq.heappop(moves)
                claimed_destinations.add(dest)
                out.add((ant, dest))
                continue

            dest = valid_dests.pop()
            claimed_destinations.add(dest)
            out.add((ant, dest))
            ant_end = monotonic()
            print(f"- ant time {round(((ant_end - ant_start) / self.time_per_turn) * 100, 3)}%")

        # if self.run_count == 1:
        #     print(f"len harvest cells {len(harvest_cells)}")
        # elif self.run_count == 50:
        #     print(food)
        # self.run_count += 1
        end = monotonic()
        print(f"move time {round(((end - start) / self.time_per_turn) * 100, 3)}%")
        return out
