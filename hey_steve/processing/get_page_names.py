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
WOOD_DIRECTS = ['Wooden_Button', 'Wooden_Door', 'Wooden_Fence', 'Fence_Gate', 'Hanging_Sign', 'Leaves',
                'Log', 'Planks', 'Wooden_Pressure_Plate', 'Sapling', 'Sign', 'Wooden_Slab', 'Wooden_Stairs', 'Wooden_Trapdoor', 'Wood']
to_add = WOOD_REDIRECTS + CORAL_REDIRECTS + COPPER_REDIRECTS
to_add.append('Infested_Block')


def calculate_items_to_remove():
    to_remove = ['Commands/give']
    for w_v in WOOD_VARIANTS:
        for w_r in WOOD_ITEM_REDIRECTS:
            to_remove.append(w_v + '_' + w_r)
    for c_v in COLOR_VARIANTS:
        for c_r in COLOR_REDIRECTS:
            to_remove.append(c_v + '_' + c_r)
    for c_v in CORAL_VARIANTS:
        for c_r in CORAL_REDIRECTS:
            to_remove.append(c_v + '_' + c_r)
    for c_v in COPPER_VARIANTS:
        for c_r in COPPER_REDIRECTS:
            to_remove.append(c_v + '_' + c_r)
    to_remove += INFESTED_BLOCKS
    return set(to_remove)


def calculate_items_to_add():
    to_add = WOOD_REDIRECTS + CORAL_REDIRECTS + COPPER_REDIRECTS
    to_add.append('Infested_Block')
    return to_add


def calculate_blocks_to_remove():
    to_remove = ['Chipped_Anvil', 'Damaged_Anvil',
                 'Light_Block', 'Planned_versions']
    for w_v in WOOD_VARIANTS:
        for w_r in WOOD_REDIRECTS:
            to_remove.append(w_v + '_' + w_r)
    for c_v in COLOR_VARIANTS:
        for c_r in COLOR_REDIRECTS:
            to_remove.append(c_v + '_' + c_r)
    for c_v in CORAL_VARIANTS:
        for c_r in CORAL_REDIRECTS:
            to_remove.append(c_v + '_' + c_r)
    for c_v in COPPER_VARIANTS:
        for c_r in COPPER_REDIRECTS:
            to_remove.append(c_v + '_' + c_r)
    to_remove += INFESTED_BLOCKS
    return set(to_remove)


def calculate_blocks_to_add():
    to_add = WOOD_REDIRECTS + CORAL_REDIRECTS + COPPER_REDIRECTS
    to_add.append('Infested_Block')
    return to_add


def extract_items():
    """
    Extract all the items from the Minecraft wiki and write them to a file.
    """

    url = "https://minecraft.wiki/w/Items"

    # try to get the content from the cache
    try:
        with open('data/downloads/Items.html', 'r') as f:
            item = f.read()
    except:
        process = subprocess.Popen(
            ['wget', '-q', '-O', 'data/downloads/Items.html', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()
        with open('data/downloads/Items.html', 'r') as f:
            item = f.read()

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = True
    h.skip_internal_links = True
    h.unicode_snob = True
    h.body_width = 0
    md = h.handle(item)

    start = md.index('## List of items')
    end = md.index('### Spawn eggs')

    list_of_items_md = md[start:end]
    matches = re.findall(r"/w/([^ ]+) ", list_of_items_md)
    items = set(matches)

    to_remove = calculate_items_to_remove()
    items = [item for item in items if item not in to_remove]

    # replace %27 with '
    items = [re.sub(r'%27', "'", item) for item in items]
    # replace \( with ( and \) with )
    items = [re.sub(r'\\', '', item) for item in items]

    items.append("Spawn_Egg")

    items = sorted(list(items))
    items = '\n'.join(items)

    with open('download_scripts/items.txt', 'w') as file:
        file.write(items)


def extract_blocks():
    """
    Extract all the blocks from the Minecraft wiki and write them to a file.
    """

    url = "https://minecraft.wiki/w/Block"

    # try to get the content from the cache
    try:
        with open('data/downloads/Block.html', 'r') as f:
            block = f.read()
    except:
        process = subprocess.Popen(
            ['wget', '-q', '-O', 'data/downloads/Block.html', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()
        with open('data/downloads/Block.html', 'r') as f:
            block = f.read()

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = True
    h.skip_internal_links = True
    h.unicode_snob = True
    h.body_width = 0
    md = h.handle(block)

    start = md.index('## List of blocks')
    end = md.index('### Technical blocks')

    list_of_blocks_md = md[start:end]

    blocks = re.findall(r"/w/([^ ]+) ", list_of_blocks_md)

    # remove all the image files
    blocks = [block for block in blocks if block[:5] != 'File:']

    # replace %27 with '
    blocks = [re.sub(r'%27', "'", block) for block in blocks]
    # replace \( with ( and \) with )
    blocks = [re.sub(r'\\', '', block) for block in blocks]

    to_remove = calculate_blocks_to_remove()
    blocks = [block for block in blocks if block not in to_remove]

    to_add = calculate_blocks_to_add()
    blocks.extend(to_add)

    blocks = sorted(set(blocks))
    blocks = '\n'.join(blocks)

    with open('download_scripts/blocks.txt', 'w') as file:
        file.write(blocks)


def extract_tutorials():
    """
    Extract all the blocks from the Minecraft wiki and write them to a file.
    """

    url = "https://minecraft.wiki/w/Tutorials"

    # try to get the content from the cache
    try:
        with open('data/downloads/Tutorials.html', 'r') as f:
            tutorials = f.read()
    except:
        process = subprocess.Popen(
            ['wget', '-q', '-O', 'data/downloads/Tutorials.html', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()
        with open('data/downloads/Tutorials.html', 'r') as f:
            tutorials = f.read()

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = True
    h.skip_internal_links = True
    h.unicode_snob = True
    h.body_width = 0
    md = h.handle(tutorials)

    pattern = r"/w/Tutorial:[^\s]+\s"
    matches = re.findall(pattern, md)

    matches = sorted(set(matches))

    matches = [match[len("/w/"):] for match in matches]

    with open("download_scripts/tutorials.txt", "w") as f:
        f.write("\n".join(matches))


def gen_name_list(filename: str):
    # Insert data into LightRAG
    with open(filename, "r") as f:
        names = f.readlines()
        names = [name.strip() for name in names]

        # Process the name a bit
        names = [name.replace(":", "_") for name in names]
        names = [name.replace("/", "_") for name in names]
        names = [name.replace("'", "_") for name in names]
        names = [name.replace("(", "_").replace(")", "_") for name in names]

    # if this is the tutorial page, we need to add _ at the end
    if filename.find("tutorials.txt") != -1:
        names = [name + "_" for name in names]
    return names


if __name__ == "__main__":
    # extract_items()
    # extract_blocks()
    # extract_tutorials()
    pass
