import heapq
import pickle
from multiprocessing import Pool

import numpy as np
from Neural_Net_Maker import create_bot
from ant_game import GameSpecification, play_game, generate_board
from random_player import RandomBot

# filter_one = 8x3x3x6
# bias_one = 8
# filter_two = 16x3x3x8
# bias_two = 16
# flat_filter = 2704x5
# flat_bias = 5


def noise_on_tuple_of_arrays(tup: tuple[np.ndarray, ...], std: float):
    return tuple(add_noise(arr, std) for arr in tup)


def add_noise(arr: np.ndarray, std: float):
    return arr + np.random.normal(0, std, arr.shape)


filter_one = np.zeros((8, 3, 3, 6))
bias_one = np.zeros((8))
filter_two = np.zeros((16, 3, 3, 8))
bias_two = np.zeros((16))
flat_filter = np.zeros((2704, 5))
flat_bias = np.zeros((5))


def play(spec, genome1):
    # genome1 = genomes[0]
    # genome2 = genomes[1]
    player_1 = create_bot(
        genome1[0], genome1[1], genome1[2], genome1[3], genome1[4], genome1[5]
    )
    player_2 = RandomBot

    return play_game(spec, player_1, player_2, visualize=False)


def find_best_ten(current_bots, std: float):
    genome = (filter_one, bias_one, filter_two, bias_two, flat_filter, flat_bias)
    genomes = []
    if len(current_bots) == 0:
        for _ in range(101):
            genomes.append(noise_on_tuple_of_arrays(genome, std))
    else:
        for bot_genome in current_bots:
            genomes.append(bot_genome)
            for _ in range(9):
                genomes.append(noise_on_tuple_of_arrays(bot_genome, std))


    inputs = []
    b = generate_board(60, 60, hills_per_player=2)
    spec = GameSpecification(b, max_turns=500)
    for i in range(0, len(genomes)-1):
        inputs.append((spec, genomes[i]))

    with Pool() as pool:
        results = pool.starmap(play, inputs)
        pool.close()
        pool.join()
    
    bot_scores = []
    tie = 0
    for i, result in enumerate(results):
        p1 = inputs[i][1]
        heapq.heappush(bot_scores, (result['p1'], tie, p1))
        tie += 1
    
    return heapq.nlargest(10, bot_scores)

if __name__ == "__main__":
    with open('final_nn_weights.pkl', 'rb') as file:
        best = pickle.load(file)
    std = 2
    for i in range(10):
        all = find_best_ten(best, std)
        best = [item[2] for item in all]
        std = 8 * std / 9
        with open(f"genome_gen_{i}.pkl", "wb") as f:
            pickle.dump(best, f)
        f.close()
