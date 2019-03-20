from numpy.random import shuffle, np
from termcolor import colored
from tqdm import tqdm

from evolution import evolve_organisms, evolve_predators
from objects.food import Food
from objects.organism import Organism
from functions.name_functions import first_gen_org_name_template
from behavior import organism_behavior, predator_behavior
from gui import plotting, make_gif
from objects.predator import Predator


def simulate_all_generations(settings):
    print(colored("Universe creation is started. "
                  "Please be patient, even God needed 7 days for this...\n", 'cyan'))
    gen_stats = []
    predators, organisms, foods = _simulate_environment(settings)
    for gen in range(0, settings['gens']):
        organisms = _simulate_one_generation(settings, predators, organisms, foods, gen)
        stats = _get_generation_stats(organisms)
        gen_stats.append(stats)

        organisms = evolve_organisms(settings, organisms, gen)
        # predators = evolve_predators(settings, predators, gen)

        _print_generation_stats(gen, stats)

        if gen in settings['plot_gens']:
            _build_generation_gif(settings, gen)

    plotting.plot_stats(settings, gen_stats)


def _simulate_environment(settings):
    foods = []
    for _ in range(0, settings['food_num']):
        foods.append(Food(settings))

    organisms = []
    for org in range(0, settings['org_num']):
        wih_init = np.random.uniform(-1, 1, (settings['hnodes'], settings['inodes']))  # mlp weights (input -> hidden)
        who_init = np.random.uniform(-1, 1, (settings['onodes'], settings['hnodes']))  # mlp weights (hidden -> output)

        organisms.append(Organism(settings, wih_init, who_init, name=first_gen_org_name_template(org)))

    predators = []
    if settings['pred_create']:
        for pred in range(0, settings['pred_num']):
            wih_init = np.random.uniform(-1, 1,
                                         (settings['hnodes'], settings['inodes']))  # mlp weights (input -> hidden)
            who_init = np.random.uniform(-1, 1,
                                         (settings['onodes'], settings['hnodes']))  # mlp weights (hidden -> output)

            predators.append(Predator(settings, wih_init, who_init, name=first_gen_org_name_template(pred)))

    return predators, organisms, foods


def _simulate_one_generation(settings, predators, organisms, foods, gen):
    total_ticks = settings['ticks']

    for tick in tqdm(range(0, total_ticks, 1), disable=True):

        shuffle(organisms)
        if gen in settings['plot_gens']:
            plotting.plot_frame(settings, predators, organisms, foods, gen, tick)

        org_vision = settings['org_vision_dist']
        for org1 in organisms:

            # action on closest food
            closest_dist = org_vision
            for food in foods:
                closest_dist = organism_behavior.behave_on_food(closest_dist,
                                                                settings['org_eat_dist'],
                                                                org1,
                                                                food)
            # action on closest predator

                closest_dist = org_vision
                for pred in predators:
                    closest_dist = organism_behavior.behave_on_predator(closest_dist,
                                                                        settings['pred_eat_dist'],
                                                                        org1,
                                                                        pred)
            # action on closest other organism
            closest_dist = org_vision
            for org2 in organisms:
                closest_dist = organism_behavior.behave_on_other_organism(closest_dist,
                                                                          settings['org_org_dist'],
                                                                          settings['org_org_penalty'],
                                                                          org1,
                                                                          org2)

        pred_vision = settings['pred_vision_dist']
        for pred1 in predators:

            closest_dist = pred_vision
            for org in organisms:
                closest_dist = predator_behavior.behave_on_organism(closest_dist,
                                                                    settings['pred_eat_dist'],
                                                                    pred1,
                                                                    org)

        # simulate food and organism response
        for food in foods:
            food.respawn(settings)

        for org in organisms:
            org.think()

        for pred in predators:
            pred.think()

    return organisms


def _get_generation_stats(generation):
    stats = {'BEST': -100, 'WORST': 100, 'SUM': 0, 'COUNT': 0}
    for org in generation:
        if org.fitness > stats['BEST']:
            stats['BEST'] = org.fitness

        if org.fitness < stats['WORST']:
            stats['WORST'] = org.fitness

        stats['SUM'] += org.fitness
        stats['COUNT'] += 1

    stats['AVG'] = stats['SUM'] / stats['COUNT']
    return stats


def _print_generation_stats(gen, stats):
    print(
        ' > GEN-' + str(gen + 1), ':',
        colored(('BEST:', np.round(stats['BEST'], 2)), 'green'),
        colored(('AVG:', np.round(stats['AVG'], 2)), 'blue'),
        colored(('WORST:', np.round(stats['WORST'], 2)), 'red')
    )


def _build_generation_gif(settings, gen):
    print(' > GEN-' + str(gen + 1), '.gif file is building...\n')
    make_gif.make_gif(settings, gen)
