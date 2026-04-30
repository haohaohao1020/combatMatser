from typing import Dict, Any, List
from characters.hero_system.character_types import HeroType, HeroArchetype, HERO_INFO
from characters.hero_system.hero_base import HeroCharacter


def create_hero(x: float, y: float, is_player1: bool, hero_type: HeroType) -> HeroCharacter:
    if hero_type == HeroType.WARRIOR_GIANT:
        from characters.hero_system.warrior_giant import WarriorGiant
        return WarriorGiant(x, y, is_player1)
    elif hero_type == HeroType.SWIFT_ASSASSIN:
        from characters.hero_system.swift_assassin import SwiftAssassin
        return SwiftAssassin(x, y, is_player1)
    elif hero_type == HeroType.MYSTIC_MAGE:
        from characters.hero_system.mystic_mage import MysticMage
        return MysticMage(x, y, is_player1)
    elif hero_type == HeroType.BASIC_FIGHTER:
        from characters.hero_system.basic_fighter import BasicFighter
        return BasicFighter(x, y, is_player1)
    else:
        from characters.hero_system.basic_fighter import BasicFighter
        return BasicFighter(x, y, is_player1)


def get_hero_info(hero_type: HeroType) -> Dict[str, Any]:
    return HERO_INFO.get(hero_type, {})


def get_all_hero_types() -> List[HeroType]:
    return list(HeroType)


def get_hero_type_by_name(name: str) -> HeroType:
    name_lower = name.lower()
    for hero_type in HeroType:
        info = HERO_INFO.get(hero_type, {})
        if info.get("name", "").lower() == name_lower:
            return hero_type
        if hero_type.name.lower() == name_lower:
            return hero_type
    return HeroType.BASIC_FIGHTER
