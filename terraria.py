from dataclasses import dataclass, field
from enum import IntEnum

from typing import Set, Union, ClassVar, Dict

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
    DUNGEON = 1
    CORRUPTION = 2
    CRIMSON = 3
    MUSHROOM = 4

    if HARD_MODE:
        HALLOW = 5

    JUNGLE = 6
    SNOW = 7
    OCEAN = 8
    DESERT = 9
    UNDERGROUND = 10
    FOREST = 11


DefSet = field(default_factory=set)
ResolvedNPCs = Set[Union[str, 'NPC']]


@dataclass
class NPC:
    name: str
    hard_mode: bool = False

    loves_npc: ResolvedNPCs = DefSet
    likes_npc: ResolvedNPCs = DefSet
    dislikes_npc: ResolvedNPCs = DefSet
    hates_npc: ResolvedNPCs = DefSet

    loves_biome: Set[Biome] = DefSet
    likes_biome: Set[Biome] = DefSet
    dislikes_biome: Set[Biome] = DefSet
    hates_biome: Set[Biome] = DefSet

    ALL_NPCs: ClassVar[Dict[str, 'NPC']]

    def __post_init__(self):
        self.ALL_NPCs[self.name] = self

    @classmethod
    def resolve(cls):
        return


NPC('Guide',
    likes_biome={Biome.FOREST}, dislikes_biome={Biome.OCEAN},
    likes_npc={'Clothier', 'Zoologist'}, dislikes_npc={'Steampunker'},
    hates_npc={'Painter'})
NPC('Merchant',
    likes_biome={Biome.FOREST}, dislikes_biome={Biome.DESERT},
    likes_npc={'Golfer', 'Nurse'}, dislikes_npc={'Tax Collector'},
    hates_npc={'Angler'})
NPC('Zoologist',
    likes_biome={Biome.FOREST}, dislikes_biome={Biome.DESERT},
    loves_npc={'Witch Doctor'}, likes_npc={'Golfer'},
    dislikes_npc={'Angler'}, hates_npc={'Arms Dealer'})
NPC('Golfer',
    likes_biome={Biome.FOREST}, dislikes_biome={Biome.Underground},
    loves_npc={'Angler'}, likes_npc={'Painter', 'Zoologist'},
    dislikes_npc={'Pirate'}, hates_npc={'Merchant'})
NPC('Nurse',
    likes_biome={Biome.HALLOW}, dislikes_biome={Biome.SNOW},
    loves_npc={'Arms Dealer'}, likes_npc={'Wizard'},
    dislikes_npc={'Dryad', 'Party Girl'}, hates_npc={'Zoologist'})
NPC('Tavernkeep',
    likes_biome={Biome.HALLOW}, dislikes_biome={Biome.SNOW},
    loves_npc={'Demolitionist'}, likes_npc={'Goblin Tinkerer'},
    dislikes_npc={'Guide'}, hates_npc={'Dye Trader'})
NPC('Party Girl',
    likes_biome={Biome.HALLOW}, dislikes_biome={Biome.UNDERGROUND},
    loves_npc={'Wizard', 'Zoologist'}, likes_npc={'Stylist'},
    dislikes_npc={'Merchant'}, hates_npc={'Tax Collector'})
NPC('Wizard',
    likes_biome={Biome.HALLOW}, dislikes_biome={Biome.OCEAN},
    loves_npc={'Golfer'}, likes_npc={'Merchant'},
    dislikes_npc={'Witch Doctor'}, hates_npc={'Cyborg'})
NPC('Demolitionist',
    likes_biome={Biome.UNDERGROUND}, dislikes_biome={Biome.OCEAN},
    loves_npc={'Tavernkeep'}, likes_npc={'Mechanic'},
    dislikes_npc={'Arms Dealer', 'Goblin Tinkerer'})
NPC('Goblin Tinkerer',
    likes_biome={Biome.UNDERGROUND}, dislikes_biome={Biome.JUNGLE},
    loves_npc={'Mechanic'}, likes_npc={'Dye Trader'},
    dislikes_npc={'Clothier'}, hates_npc={'Stylist'})
NPC('Clothier',
    likes_biome={Biome.UNDERGROUND}, dislikes_biome={Biome.HALLOW},
    loves_npc={'Truffle'}, likes_npc={'Tax Collector'},
    dislikes_npc={'Nurse'}, hates_npc={'Mechanic'})
NPC('Dye Trader',
    likes_biome={Biome.DESERT}, dislikes_biome={Biome.FOREST},
    likes_npc={'Arms Dealer', 'Painter'},
    dislikes_npc={'Steampunker'}, hates_npc={'Pirate'})
NPC('Arms Dealer',
    likes_biome={Biome.DESERT}, dislikes_biome={Biome.SNOW},
    loves_npc={'Nurse'}, likes_npc={'Steampunker'},
    dislikes_npc={'Golfer'}, hates_npc={'Demolitionist'})
NPC('Steampunker', True,
    likes_biome={Biome.DESERT}, dislikes_biome={Biome.JUNGLE},
    loves_npc={'Cyborg'}, likes_npc={'Painter'},
    dislikes_npc={'Dryad', 'Wizard', 'Party Girl'})
NPC('Dryad',
    likes_biome={Biome.JUNGLE}, dislikes_biome={Biome.DESERT},
    likes_npc={'Witch Doctor', 'Truffle'},
    dislikes_npc={'Angler'}, hates_npc={'Golfer'})
NPC('Painter',
    likes_biome={Biome.JUNGLE}, dislikes_biome={Biome.FOREST},
    loves_npc={'Dryad'}, likes_npc={'Party Girl'},
    dislikes_npc={'Truffle', 'Cyborg'})
NPC('Witch Doctor',
    likes_biome={Biome.JUNGLE}, dislikes_biome={Biome.HALLOW},
    likes_npc={'Dryad', 'Guide'},
    dislikes_npc={'Nurse'}, hates_npc={'Truffle'})
NPC('Stylist',
    likes_biome={Biome.OCEAN}, dislikes_biome={Biome.SNOW},
    loves_npc={'Dye Trader'}, likes_npc={'Pirate'},
    dislikes_npc={'Tavernkeep'}, hates_npc={'Goblin Tinkerer'})
NPC('Angler',
    likes_biome={Biome.OCEAN}, dislikes_biome={Biome.DESERT},
    likes_npc={'Demolitionist', 'Party Girl', 'Tax Collector'},
    hates_npc={'Tavernkeep'})
NPC('Pirate', True,
    likes_biome={Biome.OCEAN}, dislikes_biome={Biome.UNDERGROUND},
    loves_npc={'Angler'}, likes_npc={'Tavernkeep'},
    dislikes_npc={'Stylist'}, hates_npc={'Guide'})
NPC('Mechanic',
    likes_biome={Biome.SNOW}, dislikes_biome={Biome.UNDERGROUND},
    loves_npc={'Goblin Tinkerer'}, likes_npc={'Cyborg'},
    dislikes_npc={'Arms Dealer'}, hates_npc={'Clothier'})
NPC('Tax Collector', True,
    likes_biome={Biome.SNOW}, dislikes_biome={Biome.HALLOW},
    loves_npc={'Merchant'}, likes_npc={'Party Girl'},
    dislikes_npc={'Demolitionist', 'Mechanic'}, hates_npc={'Santa Claus'})
NPC('Cyborg', True,
    likes_biome={Biome.SNOW}, dislikes_biome={Biome.JUNGLE},
    likes_npc={'Steampunker', 'Pirate', 'Stylist'},
    dislikes_npc={'Zoologist'}, hates_npc={'Wizard'})
NPC('Santa Claus', True,
    loves_biome={Biome.SNOW}, hates_biome={Biome.DESERT},
    hates_npc={'Tax Collector'})
NPC('Truffle', True,
    likes_biome={Biome.MUSHROOM},
    loves_npc={'Guide'}, likes_npc={'Dryad'},
    dislikes_npc={'Clothier'}, hates_npc={'Witch Doctor'})
