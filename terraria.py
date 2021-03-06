from dataclasses import dataclass, field
from enum import IntEnum
from itertools import chain, combinations
from time import time

from typing import Set, Union, ClassVar, Dict, Tuple, Iterable

import numpy as np
import numpy.random
import scipy.optimize as opt


HARD_MODE = False


# Refer https://terraria.gamepedia.com/House
# These figures exclude walls
MIN_HOUSE_WIDTH = 3
MIN_HOUSE_HEIGHT = 2
MIN_HOUSE_AREA_WITH_FRAME = 60
MAX_HOUSE_AREA_WITH_FRAME = 750

# https://terraria.gamepedia.com/NPCs#Factors_affecting_Happiness
MIN_HAPPY_BUY = 0.75
MAX_HAPPY_BUY = 1.50
MIN_HAPPY_SELL = 0.67
MAX_HAPPY_SELL = 1.50


class Biome(IntEnum):
    """
    biome-related preferences will reference the primary biome where the player
    is, rather than where the NPC or its home is
    """

    # "the price multiplier will always be set to the maximum 150% if the NPC
    # is [...] located in the Corruption, Crimson, or Dungeon
    # DUNGEON = 1
    # CORRUPTION = 2
    # CRIMSON = 3

    MUSHROOM = 4
    HALLOW = 5
    JUNGLE = 6
    SNOW = 7
    OCEAN = 8
    DESERT = 9
    UNDERGROUND = 10
    FOREST = 11

    @property
    def in_hard_mode(self) -> bool:
        return self == Biome.HALLOW

    def __str__(self):
        return self.name

    @classmethod
    def from_coords(cls, quadrants: 'BiomeQuadrants', x: float, y: float) -> 'Biome':
        return quadrants[
            {
                (True, True): 0,
                (False, True): 1,
                (False, False): 2,
                (True, False): 3,
            }[x >= 0, y >= 0]
        ]


ResolvedNPCs = Tuple[Union[str, 'NPC'], ...]


@dataclass
class NPC:
    name: str
    hard_mode: bool = False

    loves_npc: ResolvedNPCs = field(default_factory=tuple)
    likes_npc: ResolvedNPCs = field(default_factory=tuple)
    dislikes_npc: ResolvedNPCs = field(default_factory=tuple)
    hates_npc: ResolvedNPCs = field(default_factory=tuple)

    loves_biome: Set[Biome] = field(default_factory=set)
    likes_biome: Set[Biome] = field(default_factory=set)
    dislikes_biome: Set[Biome] = field(default_factory=set)
    hates_biome: Set[Biome] = field(default_factory=set)

    ALL_NPCs: ClassVar[Dict[str, 'NPC']] = {}

    def __post_init__(self):
        self.ALL_NPCs[self.name] = self

    @classmethod
    def resolve(cls):
        for npc in cls.ALL_NPCs.values():
            for rel in ('loves_npc', 'likes_npc', 'dislikes_npc', 'hates_npc'):
                new_rel = tuple(
                    cls.ALL_NPCs[name]
                    for name in getattr(npc, rel)
                )
                setattr(npc, rel, new_rel)

    @classmethod
    def load_all(cls):
        cls('Guide',
            likes_biome={Biome.FOREST}, dislikes_biome={Biome.OCEAN},
            likes_npc=('Clothier', 'Zoologist',), dislikes_npc=('Steampunker',),
            hates_npc=('Painter',))
        cls('Merchant',
            likes_biome={Biome.FOREST}, dislikes_biome={Biome.DESERT},
            likes_npc=('Golfer', 'Nurse',), dislikes_npc=('Tax Collector',),
            hates_npc=('Angler',))
        cls('Zoologist',
            likes_biome={Biome.FOREST}, dislikes_biome={Biome.DESERT},
            loves_npc=('Witch Doctor',), likes_npc=('Golfer',),
            dislikes_npc=('Angler',), hates_npc=('Arms Dealer',))
        cls('Golfer',
            likes_biome={Biome.FOREST}, dislikes_biome={Biome.UNDERGROUND},
            loves_npc=('Angler',), likes_npc=('Painter', 'Zoologist',),
            dislikes_npc=('Pirate',), hates_npc=('Merchant',))
        cls('Nurse',
            likes_biome={Biome.HALLOW}, dislikes_biome={Biome.SNOW},
            loves_npc=('Arms Dealer',), likes_npc=('Wizard',),
            dislikes_npc=('Dryad', 'Party Girl',), hates_npc=('Zoologist',))
        cls('Tavernkeep',
            likes_biome={Biome.HALLOW}, dislikes_biome={Biome.SNOW},
            loves_npc=('Demolitionist',), likes_npc=('Goblin Tinkerer',),
            dislikes_npc=('Guide',), hates_npc=('Dye Trader',))
        cls('Party Girl',
            likes_biome={Biome.HALLOW}, dislikes_biome={Biome.UNDERGROUND},
            loves_npc=('Wizard', 'Zoologist',), likes_npc=('Stylist',),
            dislikes_npc=('Merchant',), hates_npc=('Tax Collector',))
        cls('Wizard',
            likes_biome={Biome.HALLOW}, dislikes_biome={Biome.OCEAN},
            loves_npc=('Golfer',), likes_npc=('Merchant',),
            dislikes_npc=('Witch Doctor',), hates_npc=('Cyborg',))
        cls('Demolitionist',
            likes_biome={Biome.UNDERGROUND}, dislikes_biome={Biome.OCEAN},
            loves_npc=('Tavernkeep',), likes_npc=('Mechanic',),
            dislikes_npc=('Arms Dealer', 'Goblin Tinkerer',))
        cls('Goblin Tinkerer',
            likes_biome={Biome.UNDERGROUND}, dislikes_biome={Biome.JUNGLE},
            loves_npc=('Mechanic',), likes_npc=('Dye Trader',),
            dislikes_npc=('Clothier',), hates_npc=('Stylist',))
        cls('Clothier',
            likes_biome={Biome.UNDERGROUND}, dislikes_biome={Biome.HALLOW},
            loves_npc=('Truffle',), likes_npc=('Tax Collector',),
            dislikes_npc=('Nurse',), hates_npc=('Mechanic',))
        cls('Dye Trader',
            likes_biome={Biome.DESERT}, dislikes_biome={Biome.FOREST},
            likes_npc=('Arms Dealer', 'Painter',),
            dislikes_npc=('Steampunker',), hates_npc=('Pirate',))
        cls('Arms Dealer',
            likes_biome={Biome.DESERT}, dislikes_biome={Biome.SNOW},
            loves_npc=('Nurse',), likes_npc=('Steampunker',),
            dislikes_npc=('Golfer',), hates_npc=('Demolitionist',))
        cls('Steampunker', True,
            likes_biome={Biome.DESERT}, dislikes_biome={Biome.JUNGLE},
            loves_npc=('Cyborg',), likes_npc=('Painter',),
            dislikes_npc=('Dryad', 'Wizard', 'Party Girl',))
        cls('Dryad',
            likes_biome={Biome.JUNGLE}, dislikes_biome={Biome.DESERT},
            likes_npc=('Witch Doctor', 'Truffle',),
            dislikes_npc=('Angler',), hates_npc=('Golfer',))
        cls('Painter',
            likes_biome={Biome.JUNGLE}, dislikes_biome={Biome.FOREST},
            loves_npc=('Dryad',), likes_npc=('Party Girl',),
            dislikes_npc=('Truffle', 'Cyborg',))
        cls('Witch Doctor',
            likes_biome={Biome.JUNGLE}, dislikes_biome={Biome.HALLOW},
            likes_npc=('Dryad', 'Guide',),
            dislikes_npc=('Nurse',), hates_npc=('Truffle',))
        cls('Stylist',
            likes_biome={Biome.OCEAN}, dislikes_biome={Biome.SNOW},
            loves_npc=('Dye Trader',), likes_npc=('Pirate',),
            dislikes_npc=('Tavernkeep',), hates_npc=('Goblin Tinkerer',))
        cls('Angler',
            likes_biome={Biome.OCEAN}, dislikes_biome={Biome.DESERT},
            likes_npc=('Demolitionist', 'Party Girl', 'Tax Collector',),
            hates_npc=('Tavernkeep',))
        cls('Pirate', True,
            likes_biome={Biome.OCEAN}, dislikes_biome={Biome.UNDERGROUND},
            loves_npc=('Angler',), likes_npc=('Tavernkeep',),
            dislikes_npc=('Stylist',), hates_npc=('Guide',))
        cls('Mechanic',
            likes_biome={Biome.SNOW}, dislikes_biome={Biome.UNDERGROUND},
            loves_npc=('Goblin Tinkerer',), likes_npc=('Cyborg',),
            dislikes_npc=('Arms Dealer',), hates_npc=('Clothier',))
        cls('Tax Collector', True,
            likes_biome={Biome.SNOW}, dislikes_biome={Biome.HALLOW},
            loves_npc=('Merchant',), likes_npc=('Party Girl',),
            dislikes_npc=('Demolitionist', 'Mechanic',), hates_npc=('Santa Claus',))
        cls('Cyborg', True,
            likes_biome={Biome.SNOW}, dislikes_biome={Biome.JUNGLE},
            likes_npc=('Steampunker', 'Pirate', 'Stylist',),
            dislikes_npc=('Zoologist',), hates_npc=('Wizard',))
        cls('Santa Claus', True,
            loves_biome={Biome.SNOW}, hates_biome={Biome.DESERT},
            hates_npc=('Tax Collector',))
        cls('Truffle', True,
            likes_biome={Biome.MUSHROOM},
            loves_npc=('Guide',), likes_npc=('Dryad',),
            dislikes_npc=('Clothier',), hates_npc=('Witch Doctor',))

        cls.resolve()
        print(f'{len(cls.ALL_NPCs)} NPCs loaded')

    def __str__(self):
        return self.name

    def biome_cost(self, biome: Biome) -> float:
        if biome in self.loves_biome: return 0.90
        if biome in self.likes_biome: return 0.95
        if biome in self.dislikes_biome: return 1.05
        if biome in self.hates_biome: return 1.10
        return 1.00

    def pair_cost(self, other: 'NPC') -> float:
        if other in self.loves_npc: return 0.90
        if other in self.likes_npc: return 0.95
        if other in self.dislikes_npc: return 1.05
        if other in self.hates_npc: return 1.10
        return 1.00

    def print_result(self, x: float, y: float, cost: np.ndarray, biome: Biome):
        overall = cost.prod()
        pairs = cost[:-4]
        worst_pair = pairs.max()
        best_pair = pairs.min()
        pair = pairs.prod()
        biome_cost = cost[-4:-1].prod()
        crowd_cost = cost[-1]

        print(
            f'{self.name:15} '
            f'{biome.name:12}'
            f'{x:6.0f} '
            f'{y:6.0f} '
            f'{overall:4.2f} '
            f'{worst_pair:4.2f} '
            f'{best_pair:4.2f} '
            f'{pair:4.2f} '
            f'{biome_cost:4.2f} '
            f'{crowd_cost:4.2f} '
        )


"""
 II I
III IV
"""
BiomeQuadrants = Tuple[Biome, Biome, Biome, Biome]


def get_allowed_biomes() -> Iterable[BiomeQuadrants]:
    """
    There are also 11 biomes. If we allow for 1-, 2- or 3-biome towns, then there are
      11 + 11C2 + 11C3
    = 11 + 11!/2!9! + 11!/3!8!
    = 11 + 11*10/2  + 11*10*9/3/2
    = 11 + 55 + 165
    = 231 different town biome combinations, maximum.

    This can be reduced by collapsing neutral biomes (crimson, corruption, and dungeon) and equivalent biomes, and taking
    into account acceptable quadrants.

    This yields 46 quadrant configurations.
    """
    # Crimson is equivalent to corruption for this purpose
    # Dungeon is also equivalent and would be more annoying to implement
    # Underground and mushroom are not upper biomes
    upper_biomes = [
        Biome.FOREST,
        Biome.DESERT,
        Biome.OCEAN,
        Biome.SNOW,
        Biome.JUNGLE,
    ]
    if HARD_MODE:
        upper_biomes.append(Biome.HALLOW)

    # Uniform biomes
    yield from (
        (b, b, b, b)
        for b in chain(upper_biomes, (Biome.UNDERGROUND, Biome.MUSHROOM))
    )

    # One biome on top, underground basement
    yield from (
        (b, b, Biome.UNDERGROUND, Biome.UNDERGROUND)
        for b in upper_biomes
    )

    for a, b in combinations(upper_biomes, 2):
        # Two upper biomes side by side
        yield a, b, b, a
        # Two biomes on top, underground basement
        yield a, b, Biome.UNDERGROUND, Biome.UNDERGROUND

    # Quarter-mushroom
    yield Biome.UNDERGROUND, Biome.UNDERGROUND, Biome.MUSHROOM, Biome.UNDERGROUND
    # Half-mushroom
    yield Biome.UNDERGROUND, Biome.UNDERGROUND, Biome.MUSHROOM, Biome.MUSHROOM


def print_quadrants(quadrants: Iterable[BiomeQuadrants]):
    for ur, ul, dl, dr in quadrants:
        print(
            f'{ul.name[:2]} {ur.name[:2]}\n'
            f'{dl.name[:2]} {dr.name[:2]}\n'
        )


NPC.load_all()
QUADRANTS = tuple(get_allowed_biomes())
print(f'{len(QUADRANTS)} quadrant layouts loaded')


def optimise(
    biomes: BiomeQuadrants,
    method: str,
    n_iters: int,
    initial_seed: int,
    show: bool = True,
    detail: bool = False,
):
    npcs = tuple(
        npc
        for npc in NPC.ALL_NPCs.values()
        if HARD_MODE or not npc.hard_mode
    )
    n = len(npcs)

    CLOSE = 25
    CMIN, CMAX = 0.75, 1.50

    rand = numpy.random.default_rng(initial_seed)

    pair_coeffs = np.array([
        [this_npc.pair_cost(other_npc) for other_npc in npcs]
        for this_npc in npcs
    ])

    def pair_cost(norms: np.ndarray) -> np.ndarray:
        α = 1
        sigmoid = 1 + np.exp(α*(norms - CLOSE))
        μ = 1 + (pair_coeffs - 1) / sigmoid
        return μ

    biome_coeffs = np.array([
        [npc.biome_cost(biome) for biome in biomes]
        for npc in npcs
    ])

    biome_sign = np.array((
        (1, -1, -1,  1),
        (1,  1, -1, -1),
    ), ndmin=3)

    def biome_cost(nodes: np.ndarray) -> np.ndarray:
        # nodes: 19x2, nodes by xy
        # biome_sign: 2x4, xy by quadrants
        # sigmoid should be per node per xy per quadrant

        α = 1
        sigmoid = (
            1 + np.exp(
                -α * biome_sign * nodes[..., np.newaxis]
            )
        ).prod(axis=1)  # collapse over the xy (2) axis

        μ = 1 + (biome_coeffs - 1)/sigmoid
        return μ

    def crowd_cost(norms: np.ndarray) -> np.ndarray:
        C = 1.04
        α1 = 1
        α2 = 50

        no_limits = (
            1 + (C - 1)/(
                1 + np.exp(α1*(norms - 25))
            )
        ).prod(axis=1)

        with_min = 1 + np.log(
            1 + np.exp(
                α2*(no_limits/C - 1)
            )
        ) / α2
        return with_min[:, np.newaxis]

    def complete_cost(par: np.ndarray) -> np.ndarray:
        # par will be 38x1 for 19 NPCs, so needs to be reshaped to 19x2
        nodes = par.reshape((-1, 2))

        # This does not take advantage of triangular symmetry
        coord_diffs = nodes[np.newaxis, :, :] - nodes[:, np.newaxis, :]
        # Frobenius over xy (2) axis
        norms = np.linalg.norm(coord_diffs, axis=2)  # 19x19

        all_costs = np.concatenate((
            pair_cost(norms),   # n=19
            biome_cost(nodes),  # 4
            crowd_cost(norms),  # 1
        ), axis=1)
        return all_costs

    def cost_sum(par: np.ndarray) -> float:
        mean = complete_cost(par).prod(axis=1).mean()
        return mean

    def initial() -> np.ndarray:
        """
        Assuming that NPCs are roughly paired, and are otherwise not within 25
        tiles of each other
        """
        pairs_per_edge = np.sqrt(n)
        edge_width = (CLOSE + 1) * (pairs_per_edge - 1)
        # This will be flattened to 2n, but whatever
        return (rand.random((n, 2)) - 0.5) * edge_width

    # Try out some options from
    # https://docs.scipy.org/doc/scipy/reference/optimize.html#global-optimization
    # basinhopping, differential_evolution, shgo, or dual_annealing

    result = opt.basinhopping(
        func=cost_sum,
        x0=initial(),
        niter=n_iters,
        T=CMAX - CMIN,  # T should be comparable to the separation between local minima
        minimizer_kwargs={
            'method': method,
        },
        seed=rand,
        disp=detail,
    )

    def print_result():
        print(f'Lowest mean cost: {result.fun:.3f}')
        print(f'Iterations: {result.nit}')

        if not detail:
            return

        print('NPC results:')

        locs = result.x.reshape((-1, 2))
        costs = complete_cost(result.x)

        print(
            f'{"NPC":15} '
            f'{"Biome":12}'
            f'{"X":>6} '
            f'{"Y":>6} '
            f'{"Tot":>4} '
            f'{"BadP":>4} '
            f'{"BesP":>4} '
            f'{"Pair":>4} '
            f'{"Biom":>4} '
            f'{"Crwd":>4} '
        )

        for npc, loc, cost_row in zip(npcs, locs, costs):
            npc.print_result(*loc, cost_row, Biome.from_coords(biomes, *loc))

    if show:
        print_result()


def try_all_methods():
    """
    So far powell and cobyla are the most promising in short tests
    """
    quad = QUADRANTS[7]
    initial_iters = 5
    target_time = 10

    for method in opt._minimize.MINIMIZE_METHODS:
        if method not in {
            'dogleg',
            'newton-cg',
            'slsqp',
            'trust-constr',
            'trust-exact',
            'trust-krylov',
            'trust-ncg',
        }:
            print(f'Method: {method}')
            t0 = time()
            optimise(quad, method, initial_iters, 0, False)
            dur = time() - t0
            print(f'{dur/initial_iters:.3f}s/iter')

            optimise(
                quad, method,
                int(target_time/dur * initial_iters),
                0, True
            )
            print()


# try_all_methods()

optimise(
    QUADRANTS[7],
    'cobyla',
    20,
    0,
    True,
    True,
)
