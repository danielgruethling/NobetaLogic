import sys
import json
import re
from typing import Dict, Set


def region_to_normalized_locations(region) -> str:
    return re.sub(r'_+', '_', region['name'].replace(' ', '_').replace('-', '_')
                  .replace('.', '').lower() + "_locations")


def json_to_ap_python(file_path):
    # Load the JSON data
    with open(file_path, 'r') as file:
        data = json.loads(file.read())

    # Generate locations.py
    locations_code = [
        "from typing import Dict, TYPE_CHECKING",
        "from BaseClasses import Location",
        "from Options import Toggle\n",
        "if TYPE_CHECKING:",
        "    from . import LWNWorld\n\n",
        "class LWNLocation(Location):",
        "    game: str = \"Little Witch Nobeta\"\n",
        "    # override constructor to automatically mark event locations as such",
        "    def __init__(self, player: int, name=\"\", code=None, parent=None):",
        "        super(LWNLocation, self).__init__(player, name, code, parent)",
        "        self.event = code is None\n\n",
        "base_id = 1\n",
    ]

    lwn_locations = [
        "lwn_locations: Dict[str, str] = {",
    ]

    location_name_groups = [
        "location_name_groups = {",
    ]

    location_group_map: Dict[str, Set[str]] = {
        "Bosses": set(),
        "Lore": set(),
        "Item": set(),
        "Chest": set(),
        "Metal Gate": set(),
        "Barrier": set(),
        "Abyss Trial": set(),
        "Teleport": set(),
        "Event": set(),
    }

    append_locations_code = [
        "def add_location_to_region(location_name, location_id, group_name, region, world):",
        "    if (group_name == \"Metal Gate\"",
        "            and world.options.shortcut_gate_behaviour.value"
                                 f" != world.options.shortcut_gate_behaviour.option_randomized):",
        "        return",
        "    elif (group_name == \"Barrier\"",
        "          and world.options.barrier_behaviour.value"
                                 " != world.options.barrier_behaviour.option_randomized):",
        "        return",
        "    elif (group_name == \"Lore\"",
        "          and world.options.randomize_lore.value"
                                 f" == world.options.randomize_lore.option_no_lore):",
        "        return",
        "    region.locations.append(LWNLocation("
                                 f"world.player, location_name, location_id, region))\n\n",
        "def append_locations(world: \"LWNWorld\"):",
    ]

    # Generate regions.py
    regions_code = [
        "from typing import Dict, Set, TYPE_CHECKING",
        "from BaseClasses import Region\n",
        "if TYPE_CHECKING:",
        "    from . import LWNWorld\n\n",
        "class LWNRegion(Region):",
        "    game: str = \"Little Witch Nobeta\"\n\n",
    ]

    lwn_regions = [
        "lwn_regions: Dict[str, Set[str]] = {"
    ]

    # Generate rules.py
    rules_code = [
        "from typing import TYPE_CHECKING\n",
        "from .options import (",
        "    Toggle,",
        "    MagicPuzzleGateBehaviour,",
        "    ShortcutGateBehaviour,",
        "    WindRequirements,",
        "    CondensedMagic,",
        "    MaxMagicLevel,",
        "    TrialKeys,",
        "    Goal,",
        "    AbyssTrialRequirement,",
        "    RandomizeLore,",
        "    BossRequirementsDifficulty,",
        "    SkipsInLogic,",
        "    DisableDarkTunnelThunderWall,",
        "    DisableDarkTunnelBridgeCollapse,",
        "    RandomizeBossSouls,",
        "    SkippableBosses, StartingArea,",
        ")",
        "from rule_builder.rules import Has, HasAny, HasAll, HasAllCounts, HasGroup, HasGroupUnique, CanReachRegion, True_",
        "from rule_builder.options import OptionFilter",
        "from rule_builder.field_resolvers import FromOption\n",
        "if TYPE_CHECKING:",
        "    from . import LWNWorld\n\n",
        "has_fire_or_thunder = HasAny(\"Fire\", \"Thunder\")",
        "has_wind_or_skip = Has(\"Wind\") | [OptionFilter(WindRequirements, WindRequirements.option_less_wind_requirements)]",
        "has_wind_or_damage_boost = Has(\"Wind\") | (Has(\"Fire\") & [OptionFilter(WindRequirements, WindRequirements.option_less_wind_requirements)])",
        "has_magic_master_requirements = (HasAllCounts({\"Arcane\": 1, \"Fire\": 1, \"Thunder\": 1, \"Ice\": 1})",
        "                        & [OptionFilter(CondensedMagic, CondensedMagic.option_true)]",
        "                        | (Has(\"Arcane\", count = FromOption(MaxMagicLevel))",
        "                            & Has(\"Fire\", count = FromOption(MaxMagicLevel))",
        "                            & Has(\"Thunder\", count = FromOption(MaxMagicLevel))",
        "                            & Has(\"Ice\", count = FromOption(MaxMagicLevel)))",
        "                        & [OptionFilter(CondensedMagic, CondensedMagic.option_false)])",
        "has_goal_requirements = ((has_magic_master_requirements",
        "                         & [OptionFilter(Goal, Goal.option_magic_master)])",
        "                         | (HasAll(\"Specter Armor Token\", \"Tania Token\", \"Monica Token\", \"Enraged Armor Token\",",
        "                                   \"Vanessa Token\", \"Vanessa V2 Token\") & [OptionFilter(Goal, Goal.option_boss_hunt)])",
        "                         | (HasGroupUnique(\"Lore\", 99) & [OptionFilter(Goal, Goal.option_lore_keeper), OptionFilter(RandomizeLore, RandomizeLore.option_vanilla), OptionFilter(StartingArea, StartingArea.option_shrine, operator=\"ne\")])",
        "                         | (HasGroupUnique(\"Lore\", 102) & [OptionFilter(Goal, Goal.option_lore_keeper), OptionFilter(RandomizeLore, RandomizeLore.option_vanilla)])",
        "                         | (HasGroupUnique(\"Lore\", 103) & [OptionFilter(Goal, Goal.option_lore_keeper), OptionFilter(RandomizeLore, RandomizeLore.option_randomized)])",
        "                         | [OptionFilter(Goal, Goal.option_vanilla)])",
        "has_abyss_trial_requirements = ((has_magic_master_requirements",
        "                         & [OptionFilter(AbyssTrialRequirement, AbyssTrialRequirement.option_magic_master)])",
        "                         | (HasAll(\"Specter Armor Token\", \"Tania Token\", \"Monica Token\", \"Enraged Armor Token\",",
        "                                   \"Vanessa Token\", \"Vanessa V2 Token\") & [OptionFilter(AbyssTrialRequirement, AbyssTrialRequirement.option_boss_hunt)])",
        "                         | (HasGroupUnique(\"Lore\", 99) & [OptionFilter(AbyssTrialRequirement, AbyssTrialRequirement.option_lore_keeper), OptionFilter(RandomizeLore, RandomizeLore.option_vanilla), OptionFilter(StartingArea, StartingArea.option_shrine, operator=\"ne\")])",
        "                         | (HasGroupUnique(\"Lore\", 102) & [OptionFilter(AbyssTrialRequirement, AbyssTrialRequirement.option_lore_keeper), OptionFilter(RandomizeLore, RandomizeLore.option_vanilla)])",
        "                         | (HasGroupUnique(\"Lore\", 103) & [OptionFilter(AbyssTrialRequirement, AbyssTrialRequirement.option_lore_keeper), OptionFilter(RandomizeLore, RandomizeLore.option_randomized)])",
        "                         | (Has(\"Abyss Underground Trial Clear\") & Has(\"Abyss Lava Ruins Trial Clear\") & Has(\"Abyss Dark Tunnel Trial Clear\") & [OptionFilter(AbyssTrialRequirement, AbyssTrialRequirement.option_randomized_item)])",
        "                         | (Has(\"Abyss Underground Trial Clear\") & Has(\"Abyss Lava Ruins Trial Clear\") & Has(\"Abyss Dark Tunnel Trial Clear\") & [OptionFilter(AbyssTrialRequirement, AbyssTrialRequirement.option_vanilla)]))",
        "\n",
        "def has_barrier(barrier: str):",
        "    return (Has(barrier, options=[OptionFilter(MagicPuzzleGateBehaviour, MagicPuzzleGateBehaviour.option_randomized)])",
        "            | [OptionFilter(MagicPuzzleGateBehaviour, MagicPuzzleGateBehaviour.option_always_open)])",
        "\n",
        "def has_gate(gate: str):",
        "    return (Has(gate, options=[OptionFilter(ShortcutGateBehaviour, ShortcutGateBehaviour.option_randomized)])",
        "            | [OptionFilter(ShortcutGateBehaviour, ShortcutGateBehaviour.option_always_open)])",
        "\n",
        "barrier_vanilla = [OptionFilter(MagicPuzzleGateBehaviour, MagicPuzzleGateBehaviour.option_vanilla)]",
        "barrier_randomized = [OptionFilter(ShortcutGateBehaviour, ShortcutGateBehaviour.option_randomized)]",
        "gate_vanilla = [OptionFilter(ShortcutGateBehaviour, ShortcutGateBehaviour.option_vanilla)]",
        "boss_req_easy = True_() & [OptionFilter(BossRequirementsDifficulty, BossRequirementsDifficulty.option_easy)]",
        "boss_req_normal = True_() & [OptionFilter(BossRequirementsDifficulty, BossRequirementsDifficulty.option_normal)]",
        "boss_req_absorption = True_() & [OptionFilter(BossRequirementsDifficulty, BossRequirementsDifficulty.option_absorption_only)]",
        "boss_req_none = True_() & [OptionFilter(BossRequirementsDifficulty, BossRequirementsDifficulty.option_no_requirements)]",
        "boss_souls_vanilla = True_() & [OptionFilter(RandomizeBossSouls, False)]",
        "skip_boss_enabled = True_() & [OptionFilter(SkippableBosses, True)]",
        "\n",
        "def set_region_rules(world: \"LWNWorld\") -> None:",
        "    multiworld = world.multiworld",
        "    player = world.player",
        "",
    ]

    location_rules = []

    for region in data['regions']:
        if 'locations' in region and region['locations']:
            region_locations = region_to_normalized_locations(region)
            lwn_locations.append(f"    **{region_locations},")
            region_locations += ": Dict[str, str] = {"
            locations_code.append(f"{region_locations}")
            for location in region['locations']:
                if 'name' in location and 'group' in location:
                    locations_code.append(f"    \"{location['name']}\": \"{location['group']}\",")
                else:
                    locations_code.append(f"    \"{location['name']}\": \"Item\",")
                if 'rules' in location:
                    if 'group' in location:
                        if location['group'] == "Barrier":
                            location_rules.append(f"    if options.barrier_behaviour.value == options.barrier_behaviour.option_randomized:")
                            location_rules.append(f"        world.set_rule(multiworld.get_location(\"{location['name']}\", player),")
                            subbed_rule = re.sub(' \\| ', r"\n                 | ", location['rules'])
                            subbed_rule = re.sub(' & ', r"\n                 & ", subbed_rule)
                            location_rules.append(f"                 {subbed_rule})")
                        elif location['group'] == "Metal Gate":
                            location_rules.append(f"    if options.shortcut_gate_behaviour.value == options.shortcut_gate_behaviour.option_randomized:")
                            location_rules.append(f"        world.set_rule(multiworld.get_location(\"{location['name']}\", player),")
                            subbed_rule = re.sub(' \\| ', r"\n                 | ", location['rules'])
                            subbed_rule = re.sub(' & ', r"\n                 & ", subbed_rule)
                            location_rules.append(f"                 {subbed_rule})")
                        elif location['group'] == "Lore":
                            location_rules.append(f"    if world.options.randomize_lore.value != world.options.randomize_lore.option_no_lore:")
                            location_rules.append(f"        world.set_rule(multiworld.get_location(\"{location['name']}\", player),")
                            subbed_rule = re.sub(' \\| ', r"\n                 | ", location['rules'])
                            subbed_rule = re.sub(' & ', r"\n                 & ", subbed_rule)
                            location_rules.append(f"                 {subbed_rule})")
                        else:
                            location_rules.append(f"    world.set_rule(multiworld.get_location(\"{location['name']}\", player),")
                            subbed_rule = re.sub(' \\| ', r"\n             | ", location['rules'])
                            subbed_rule = re.sub(' & ', r"\n             & ", subbed_rule)
                            location_rules.append(f"             {subbed_rule})")
                    else:
                        location_rules.append(f"    world.set_rule(multiworld.get_location(\"{location['name']}\", player),")
                        subbed_rule = re.sub(' \\| ', r"\n             | ", location['rules'])
                        subbed_rule = re.sub(' & ', r"\n             & ", subbed_rule)
                        location_rules.append(f"             {subbed_rule})")
                if 'group' in location:
                    location_group_map[location['group']].add(location['name'])
            locations_code.append("}\n")
            if region['name'] == "Shrine - Start" or region['name'] == "Shrine - After first magic switch" or region['name'] == "Shrine - Cat Room":
                append_locations_code.append(f"    if world.options.starting_area == world.options.starting_area.option_shrine\\")
                append_locations_code.append(f"            or world.options.barrier_behaviour.value == world.options.barrier_behaviour.option_randomized:")
                append_locations_code.append(f"        for location_name in {region_to_normalized_locations(region)}:")
                append_locations_code.append(f"            location_id = location_name_to_id[location_name]")
                append_locations_code.append(
                    f"            group_name = {region_to_normalized_locations(region)}[location_name]")
                append_locations_code.append(
                    f"            region = world.multiworld.get_region(\"{region['name']}\", world.player)")
                append_locations_code.append(
                    f"            add_location_to_region(location_name, location_id, group_name, region, world)\n")
            else:
                append_locations_code.append(f"    for location_name in {region_to_normalized_locations(region)}:")
                if region['name'] != "Abyss - Nonota":
                    append_locations_code.append(f"        location_id = location_name_to_id[location_name]")
                else:
                    append_locations_code.append(f"        if location_name != \"Abyss - Nonota\":")
                    append_locations_code.append(f"            location_id = location_name_to_id[location_name]")
                    append_locations_code.append(f"        else:")
                    append_locations_code.append(f"            location_id = None")
                append_locations_code.append(f"        group_name = {region_to_normalized_locations(region)}[location_name]")
                append_locations_code.append(f"        region = world.multiworld.get_region(\"{region['name']}\", world.player)")
                append_locations_code.append(f"        add_location_to_region(location_name, location_id, group_name, region, world)\n")

        lwn_region = f"    \"{region['name']}\": "
        if 'exits' in region and region['exits']:
            lwn_region += "{"
            for region_exit in region['exits']:
                lwn_region += f"\"{region_exit['name']}\", "
                rule = region_exit['rules'] if isinstance(region_exit['rules'], str) else "True"
                if rule.find(" | ") >= 0 or rule.find(" & ") >= 0:
                    rule = "(" + rule + ")"
                subbed_rule = re.sub(' \\| ', r"\n                       | ", rule)
                subbed_rule = re.sub(' & ', r"\n                       & ", subbed_rule)
                rules_code.append(f"    world.set_rule(multiworld.get_entrance(\"{region['name']} -> "
                                  f"{region_exit['name']}\", player),\n"
                                  f"                   {subbed_rule})")
            lwn_region = lwn_region[:-2]
            lwn_region += "},"
        else:
            lwn_region += "set(),"
        lwn_regions.append(lwn_region)

    locations_code.append('\n'.join(lwn_locations))
    locations_code.append("}\n")

    locations_code.append("location_name_to_id: Dict[str, int] "
                          "= {name: base_id + index for index, name in enumerate(sorted(lwn_locations))}\n")

    for loc_group_name in location_group_map.keys():
        location_name_groups.append(f"    \"{loc_group_name}\": {{")
        for loc in sorted(location_group_map[loc_group_name]):
            location_name_groups.append(f"        \"{loc}\",")
        location_name_groups.append("    },")
    location_name_groups.append("}\n")

    locations_code.append(('\n'.join(location_name_groups)) + '\n')
    locations_code.append('\n'.join(append_locations_code))

    regions_code.append('\n'.join(lwn_regions))
    regions_code.append("}")

    regions_code.append("\n\ndef set_start_region(world: \"LWNWorld\"):")
    regions_code.append("    options = world.options\n")
    regions_code.append("    if options.starting_area.value == options.starting_area.option_shrine:")
    regions_code.append("        world.origin_region_name = \"Shrine - Start\"")
    regions_code.append("    elif options.starting_area.value == options.starting_area.option_underground:")
    regions_code.append("        world.origin_region_name = \"Underground - Start\"")
    regions_code.append("    elif options.starting_area.value == options.starting_area.option_lava_ruins:")
    regions_code.append("        world.origin_region_name = \"Lava Ruins - Start\"")
    regions_code.append("    elif options.starting_area.value == options.starting_area.option_dark_tunnel:")
    regions_code.append("        world.origin_region_name = \"Dark Tunnel - Start\"\n")

    rules_code.append("\n\ndef set_location_rules(world: \"LWNWorld\") -> None:")
    rules_code.append("    multiworld = world.multiworld")
    rules_code.append("    player = world.player")
    rules_code.append("    options = world.options\n")
    rules_code.append('\n'.join(location_rules))
    rules_code.append('')

    # Write to locations.py
    with open('locations.py', 'w') as file:
        file.write('\n'.join(locations_code))

    # Write to regions.py
    with open('regions.py', 'w') as file:
        file.write('\n'.join(regions_code))

    # Write to rules.py
    with open('rules.py', 'w') as file:
        file.write('\n'.join(rules_code))

    print("Files generated successfully.")


if __name__ == "__main__":
    path = str(sys.argv[1])
    json_to_ap_python(path)
