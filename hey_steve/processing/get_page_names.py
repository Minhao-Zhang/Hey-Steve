import re
import subprocess
import html2text

# Variants
WOOD_VARIANTS = ['Oak', 'Spruce', 'Birch', 'Jungle', 'Acacia', 'Dark_Oak',
                 'Mangrove', 'Cherry', 'Pale_Oak', 'Crimson', 'Warped', 'Azalea', 'Bamboo']
COLOR_VARIANTS = ['White', 'Light_Gray', 'Gray', 'Black', 'Brown', 'Red', 'Orange', 'Yellow',
                  'Lime', 'Green', 'Cyan', 'Light_Blue', 'Blue', 'Purple', 'Magenta', 'Pink']
CORAL_VARIANTS = ['Tube', 'Brain', 'Bubble', 'Fire', 'Horn',
                  'Dead_Tube', 'Dead_Brain', 'Dead_Bubble', 'Dead_Fire', 'Dead_Horn']
COPPER_VARIANTS = ['Waxed', 'Waxed_Exposed', 'Waxed_Weathered',
                   'Waxed_Oxidized', 'Exposed', 'Weathered', 'Oxidized']

# Items
WOOD_ITEM_REDIRECTS = ['Boat', 'Boat_with_Chest']

# Blocks
WOOD_REDIRECTS = ['Button', 'Door', 'Fence', 'Fence_Gate', 'Hanging_Sign', 'Leaves',
                  'Log', 'Planks', 'Pressure_Plate', 'Sapling', 'Sign', 'Slab', 'Stairs', 'Trapdoor', 'Wood', 'Hyphae', 'Stem']
COLOR_REDIRECTS = ['Candle', 'Carpet', 'Concrete', 'Concrete_Powder', 'Glazed_Terracotta', 'Shulker_Box', 'Stained_Glass',
                   'Stained_Glass_Pane', 'Terracotta', 'Wool', 'Bed', 'Banner', 'Bundle']
CORAL_REDIRECTS = ['Coral', 'Coral_Block', 'Coral_Fan']
COPPER_REDIRECTS = ['Block_of_Copper', 'Chiseled_Copper', 'Copper_Bulb', 'Copper_Door', 'Copper_Grate', 'Copper_Trapdoor',
                    'Cut_Copper', 'Cut_Copper_Slab', 'Cut_Copper_Stairs']

INFESTED_BLOCKS = ['Infested_Chiseled_Stone_Bricks', 'Infested_Cracked_Stone_Bricks', 'Infested_Mossy_Stone_Bricks',
                   'Infested_Stone', 'Infested_Stone_Bricks', 'Infested_Cobblestone', 'Infested_Mossy_Cobblestone']

# Helper Functions


def get_html_content(local_path, url=None):
    """Fetch HTML content from cache or download if missing."""
    if url:
        try:
            with open(local_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            subprocess.run(['wget', '-q', '-O', local_path, url], check=True)
            with open(local_path, 'r', encoding='utf-8') as f:
                return f.read()
    else:
        with open(local_path, 'r', encoding='utf-8') as f:
            return f.read()


def html_to_markdown(html_content):
    """Convert HTML content to markdown using predefined settings."""
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = True
    h.skip_internal_links = True
    h.unicode_snob = True
    h.body_width = 0
    return h.handle(html_content)


def extract_markdown_section(markdown, start_marker, end_marker):
    """Extract a section of markdown between two markers."""
    start = markdown.index(start_marker)
    end = markdown.index(end_marker)
    return markdown[start:end]


def extract_links_with_regex(markdown_section, pattern=r"/w/([^\s]+) "):
    """Extract wiki links using a regex pattern."""
    return re.findall(pattern, markdown_section)


def extract_links_from_table_column(markdown_table, column_index=0):
    """Extract links from a specific column in a markdown table."""
    pattern = re.compile(r"/w/([^\s]+) ")
    extracted = []
    for line in markdown_table.splitlines():
        parts = line.strip().split('|')
        if len(parts) > column_index and len(parts) > 1:
            column_content = parts[column_index].strip()
            match = pattern.search(column_content)
            if match and not match.group(1).startswith('File:'):
                extracted.append(match.group(1))
    return extracted


def generate_redirect_combinations(variants, redirects):
    """Generate all combinations of variants and redirects."""
    return [f"{variant}_{redirect}" for variant in variants for redirect in redirects]


def generate_removal_list(initial_removals, variant_redirect_pairs, additional_removals):
    """Generate a list of items to remove based on initial, variant-redirect pairs, and additional removals."""
    to_remove = initial_removals.copy()
    for variants, redirects in variant_redirect_pairs:
        to_remove += generate_redirect_combinations(variants, redirects)
    to_remove += additional_removals
    return set(to_remove)


def generate_addition_list(redirect_lists, additional_items):
    """Generate a list of items to add by combining redirect lists and additional items."""
    to_add = []
    for rlist in redirect_lists:
        to_add.extend(rlist)
    to_add += additional_items
    return to_add


def sanitize_names(names):
    """Sanitize names by replacing problematic characters."""
    sanitized = []
    for name in names:
        name = re.sub(r'%27', "'", name)
        name = re.sub(r'\\', '', name)
        sanitized.append(name)
    return sanitized


def write_to_file(filename, items):
    """Write a list of items to a file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(items)))

# Removal and Addition List Generators


def calculate_items_to_remove():
    variant_redirect_pairs = [
        (WOOD_VARIANTS, WOOD_ITEM_REDIRECTS),
        (COLOR_VARIANTS, COLOR_REDIRECTS),
        (CORAL_VARIANTS, CORAL_REDIRECTS),
        (COPPER_VARIANTS, COPPER_REDIRECTS),
    ]

    return generate_removal_list(
        ['Commands/give'],
        variant_redirect_pairs,
        INFESTED_BLOCKS
    )


def calculate_blocks_to_remove():
    variant_redirect_pairs = [
        (WOOD_VARIANTS, WOOD_REDIRECTS),
        (COLOR_VARIANTS, COLOR_REDIRECTS),
        (CORAL_VARIANTS, CORAL_REDIRECTS),
        (COPPER_VARIANTS, COPPER_REDIRECTS),
    ]
    return generate_removal_list(
        ['Chipped_Anvil', 'Damaged_Anvil', 'Light_Block', 'Planned_versions'],
        variant_redirect_pairs,
        INFESTED_BLOCKS
    )


def calculate_items_to_add():
    return generate_addition_list(
        [WOOD_REDIRECTS, CORAL_REDIRECTS, COPPER_REDIRECTS],
        ['Infested_Block']
    )


def calculate_blocks_to_add():
    return calculate_items_to_add()  # Same as items_to_add

# Extraction Functions


def extract_biomes():
    html_content = get_html_content('data/downloads/Biome.html')
    md = html_to_markdown(html_content)
    section = extract_markdown_section(
        md, '## List of biomes', '### Unused biomes')
    biomes = extract_links_from_table_column(section)
    biomes = [bio for bio in biomes if not bio.startswith('Biome')]
    biomes = sanitize_names(biomes)
    write_to_file('download_scripts/biome.txt', sorted(set(biomes)))


def extract_blocks():
    html_content = get_html_content('data/downloads/Block.html')
    md = html_to_markdown(html_content)
    section = extract_markdown_section(
        md, '## List of blocks', '### Technical blocks')
    blocks = extract_links_with_regex(section)
    blocks = [block for block in blocks if not block.startswith(
        'File:') and not block.startswith("Stripped")]
    blocks = sanitize_names(blocks)
    blocks = [block for block in blocks if block not in calculate_blocks_to_remove()]
    blocks += calculate_blocks_to_add()
    blocks.append("Stripped_Log")
    write_to_file('download_scripts/block.txt', sorted(set(blocks)))


def extract_effects():
    html_content = get_html_content('data/downloads/Effect.html')
    md = html_to_markdown(html_content)
    section = extract_markdown_section(
        md, '## Effect list', '### Descriptions')
    effects = extract_links_with_regex(section)
    effects = sanitize_names(effects)
    effects = [e for e in effects if not e.startswith("Effect?")]
    write_to_file('download_scripts/effect.txt', sorted(set(effects)))


def extract_enchantments():
    html_content = get_html_content('data/downloads/Enchanting.html')
    md = html_to_markdown(html_content)
    section = extract_markdown_section(
        md, '## Summary of enchantments', '## Summary of enchantments by item')
    enchants = extract_links_from_table_column(section)
    enchants = sanitize_names(enchants)
    enchants.remove("Enchanting?section=9&veaction=edit")
    write_to_file('download_scripts/enchantment.txt', sorted(set(enchants)))


def extract_mobs():
    html_content = get_html_content('data/downloads/Mob.html')
    md = html_to_markdown(html_content)
    section = extract_markdown_section(
        md, '## List of mobs', '### Unused mobs')
    mobs = extract_links_with_regex(section)
    mobs.remove("Bossbar")
    write_to_file('download_scripts/mob.txt', sorted(set(mobs)))


def extract_items():
    html_content = get_html_content('data/downloads/Item.html')
    md = html_to_markdown(html_content)
    section = extract_markdown_section(
        md, '## List of items', '### Spawn eggs')
    items = extract_links_with_regex(section)
    items = sanitize_names(items)
    items = [item for item in items if item not in calculate_items_to_remove()]
    items.append('Spawn_Egg')
    write_to_file('download_scripts/item.txt', sorted(set(items)))


def extract_smithing():
    html_content = get_html_content('data/downloads/Smithing.html')
    md = html_to_markdown(html_content)
    section = extract_markdown_section(
        md, '### Template', '### Material')
    smithing = extract_links_with_regex(section)
    smithing = sanitize_names(smithing)
    smithing = [s for s in smithing if not s.startswith("Smithing?")]
    write_to_file('download_scripts/smithing.txt', sorted(set(smithing)))


def extract_structure():
    html_content = get_html_content('data/downloads/Structure.html')
    md = html_to_markdown(html_content)
    section = extract_markdown_section(
        md, '## Overworld', '## Removed structures')
    structure = extract_links_from_table_column(section)
    structure = sanitize_names(structure)
    structure = [s for s in structure if not s.startswith("Structure?")]
    write_to_file('download_scripts/structure.txt', sorted(set(structure)))


def extract_tutorials():
    html_content = get_html_content('data/downloads/Tutorials.html')
    md = html_to_markdown(html_content)
    tutorials = extract_links_with_regex(md, r"/w/(Tutorial:[^\s]+) ")
    tutorials = sanitize_names(tutorials)
    write_to_file('download_scripts/tutorials.txt', sorted(set(tutorials)))


def gen_name_list(filename: str):
    """Generate sanitized name list from a file."""
    with open(filename, 'r', encoding='utf-8') as f:
        names = [name.strip() for name in f.readlines()]
        names = [name.replace(":", "_").replace(
            "/", "_").replace("'", "_").replace("(", "_").replace(")", "_") for name in names]
        if "tutorials.txt" in filename:
            names = [name + "_" for name in names]
    return names


if __name__ == "__main__":
    extract_items()
    extract_blocks()
    extract_tutorials()
    extract_enchantments()
    extract_biomes()
    extract_mobs()
    extract_effects()
    extract_smithing()
    extract_structure()
