import pygame, sys, random, time, math

# Initialize Pygame
pygame.init()

chest_interacted = False  # Tracks if the chest interaction key has already been handled

def get_room_colors(tier):
    """
    Returns a color scheme for the room based on its tier.
    :param tier: The current tier of the room.
    :return: A dictionary with background and wall colors.
    """
    # Define muted, dungeon-appropriate colors
    color_schemes = [
        {"bg": (30, 30, 30), "wall": (80, 80, 80)},    # Tier 1
        {"bg": (40, 35, 30), "wall": (90, 80, 70)},    # Tier 2
        {"bg": (35, 30, 40), "wall": (85, 75, 90)},    # Tier 3
        {"bg": (30, 40, 35), "wall": (80, 90, 85)},    # Tier 4
        {"bg": (40, 40, 30), "wall": (100, 100, 75)},  # Tier 5
        {"bg": (30, 30, 45), "wall": (70, 70, 100)},   # Tier 6
        {"bg": (25, 35, 25), "wall": (60, 80, 60)},    # Tier 7
        {"bg": (50, 40, 30), "wall": (110, 90, 70)},   # Tier 8
        {"bg": (35, 35, 35), "wall": (100, 100, 100)}, # Tier 9
        {"bg": (20, 20, 20), "wall": (60, 60, 60)},    # Tier 10+
    ]

    # Clamp tier to available schemes
    capped_tier = min(tier, len(color_schemes))
    return color_schemes[capped_tier - 1]

def calculate_final_stats(damage=0):
    """
    Calculates the player's final stats based on base stats and equipped items.
    :param damage: The amount of damage to apply to the player's health.
    :return: A dictionary of the final stats.
    """
    final_stats = player_stats.copy()
    
    # Add stats from equipped weapon
    if equipment["Weapons"]:
        weapon = equipment["Weapons"][0]
        for stat, value in weapon["Stats"].items():
            if stat in final_stats:
                final_stats[stat] += value

    # Add stats from equipped armor
    if equipment["Armor"]:
        armor = equipment["Armor"][0]
        for stat, value in armor["Stats"].items():
            if stat == "Health":  # Health on armor increases MaxHealth
                final_stats["MaxHealth"] += value
            elif stat in final_stats:
                final_stats[stat] += value
    
    # Add stats from Wildboys
    for wildboy in equipment["Wildboys"]:
        for stat, value in wildboy["Stats"].items():
            if stat in final_stats:
                final_stats[stat] += value
    
    
    # Apply damage with modifiers
    if damage > 0:
        effective_damage = max(1, damage - final_stats["Armor"])  # Minimum of 1 damage
        final_stats["Health"] -= effective_damage
        # Update the global player_stats with the new health
        player_stats["Health"] = final_stats["Health"]

    # Ensure current Health does not exceed MaxHealth
    final_stats["Health"] = min(final_stats["Health"], final_stats["MaxHealth"])
    player_stats["Health"] = final_stats["Health"]  # Sync with player_stats
    return final_stats

# Levelgate
levelgate_rect = None
levelgate_spawned = False  
levelgate_used = False  
levelgate_should_spawn = False  

# Health Fountain
health_fountain_rect = None
COLOR_FOUNTAIN = (255, 150, 150)  # Light red color for the fountain
fountain_spawned = False  # Tracks if the health fountain has been spawned
fountain_used = False  # Tracks if the player has already used the fountain
fountain_should_spawn = False  # Tracks if the fountain should spawn in the next room

# Chest checker
chest_rect = None  # Will store the chest rectangle
chest_spawned = False  # Tracks if the chest has already been spawned
COLOR_CHEST = (150, 100, 50)  # Chest color for visualization
chest_opened = False  # Flag to track if the chest has been opened
chest_item = None  # Tracks the item currently in the chest

def select_random_wildboys():
    """
    Randomly selects three Wildboys from the WILDBOYS list.
    Ensures the selection doesn't exceed the available Wildboys.
    """
    return random.sample(WILDBOYS, min(3, len(WILDBOYS)))

def add_to_inventory(item, item_type):
    """
    Adds an item to the inventory while respecting the cap of 3 items.
    :param item: The item to add (dict with 'Name' and 'Stats').
    :param item_type: The type of item ('Weapons' or 'Armor').
    """
    if item_type not in inventory:
        return
    
    if len(inventory[item_type]) < 3:
        inventory[item_type].append(item)
    else:
        print(f"Cannot add {item['Name']} to {item_type}. Inventory is full!")

# Window settings
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dungeon Prototype")

# Colors
COLOR_BG = (30, 30, 30)
COLOR_PLAYER = (200, 200, 50)
COLOR_WALL = (100, 100, 100)
COLOR_ENEMY = (200, 50, 50)
COLOR_HEALTH_BG = (100, 0, 0)
COLOR_HEALTH = (200, 0, 0)
COLOR_GAME_OVER = (255, 255, 255)
COLOR_SWORD = (150, 150, 150)  # Just to visualize the sword hit area

def generate_equipment(tier, equipment_type):
    """Generate a weapon or armor based on tier."""
    # Define the stat ranges for weapons and armor
    stat_ranges = {
        "Weapon": {
            "AttackLength": [(15, 25), (15, 50), (15, 60), (15, 70), (15, 90), (15, 110), (15, 120), (15, 130), (15, 140), (15, 150), (15, 160)],
            "AttackWidth": [(15, 25), (15, 50), (15, 60), (15, 70), (15, 90), (15, 110), (15, 120), (15, 130), (15, 140), (15, 150), (15, 160)],
            "AttackDamage": [(4, 5), (5, 10), (8, 15), (12, 20), (15, 30), (20, 50), (25, 60), (30, 70), (35, 80), (40, 90), (45, 100)],
        },
        "Armor": {
            "Armor": [(0, 0), (1, 3), (2, 5), (3, 7), (4, 10), (5, 15), (6, 18), (7, 20), (8, 22), (9, 24), (10, 25)],
            "Health": [(0, 0), (10, 20), (15, 30), (20, 40), (25, 50), (30, 60), (35, 70), (40, 80), (45, 90), (50, 100), (55, 110)],
            "AttackSpeed": [(0, 0), (-0.3, 0.3), (-0.4, 0.4), (-0.5, 0.5), (-0.6, 0.6), (-0.7, 0.7), (-0.8, 0.8), (-0.9, 0.9), (-1.0, 1.0), (-1.1, 1.1), (-1.2, 1.2)],
            "MovementSpeed": [(0, 0), (-1, 1), (-1, 2), (0, 3), (1, 4), (2, 5), (3, 6), (4, 7), (5, 8), (6, 9), (7, 10)],
        },
    }

    # Special handling for starter weapon (tier 0)
    if tier == 0 and equipment_type == "Weapon":
        stats = {
            "AttackLength": random.randint(*stat_ranges["Weapon"]["AttackLength"][0]),
            "AttackWidth": random.randint(*stat_ranges["Weapon"]["AttackWidth"][0]),
            "AttackDamage": random.randint(*stat_ranges["Weapon"]["AttackDamage"][0]),
        }
        name = "Starter Weapon"
        return {"Name": name, "Stats": stats}

    # Adjust tier for indexing (tier 1 corresponds to index 1)
    tier_index = min(max(1, tier), 10)  # Clamp to valid range (1-10)

    # Generate stats
    stats = {stat: round(random.uniform(*stat_ranges[equipment_type][stat][tier_index]), 2) if "AttackSpeed" in stat
             else random.randint(*stat_ranges[equipment_type][stat][tier_index])
             for stat in stat_ranges[equipment_type]}

    # Generate names with broader conditions for prefixes and suffixes
    if equipment_type == "Weapon":
        prefixes = ["Keen", "Long", "Broad", "Deadly", "Sharp"]
        suffixes = ["Blade", "Cleaver", "Sword", "Axe", "Dagger"]
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
    elif equipment_type == "Armor":
        prefixes = ["Sturdy", "Vital", "Swift", "Resilient", "Fortified"]
        suffixes = ["Vest", "Mail", "Plate", "Guard", "Shield"]
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)

    # Add conditions to further refine the naming logic
    if equipment_type == "Weapon":
        if stats["AttackDamage"] > 50:
            prefix = "Deadly"
        elif stats["AttackLength"] > stats["AttackWidth"] + 10:
            prefix = "Long"
        elif stats["AttackWidth"] > stats["AttackLength"] + 10:
            suffix = "Cleaver"
    elif equipment_type == "Armor":
        if stats["Armor"] > 15:
            prefix = "Fortified"
        elif stats["Health"] > 50:
            prefix = "Vital"
        elif abs(stats["AttackSpeed"]) < 0.5:
            suffix = "Mail"

    # Generate the name and return the result
    name = f"{prefix} Level {tier} {suffix}"
    return {"Name": name, "Stats": stats}

# Default Player Stats
DEFAULT_PLAYER_STATS = {
    "Health": 100,
    "MaxHealth": 100,
    "Armor": 0,
    "AttackDamage": 10,
    "AttackSpeed": 2.0,    # attacks per second
    "AttackLength": 0,  # length of sword attack
    "AttackWidth": 0,   # width of sword attack
    "MovementSpeed": 2,
    "DashDistance": 250,
    "DashCooldown": 1
}

# Define possible Wildboys
WILDBOYS = [
    {
        "Name": "Wildboy of Girth + 20 AD (if MH > 120)",
        "Stats": {"AttackDamage": 20},
        "Condition": lambda stats: stats["MaxHealth"] > 120  
    },
    {
        "Name": "Wildboy of Slow + 5 A (if MS < 2)",
        "Stats": {"Armor": 5},
        "Condition": lambda stats: stats["MovementSpeed"] < 2  
    },
    {
        "Name": "Wildboy of Wilding + 200 W (if A = 0)",
        "Stats": {"AttackWidth": 200},
        "Condition": lambda stats: stats["Armor"] == 0  # 
    },
    {
        "Name": "Wildboy of Quick + 4.0 AS (if AD < 15)",
        "Stats": {"AttackSpeed": 4.0},
        "Condition": lambda stats: stats["AttackDamage"] < 15
    },
    {
        "Name": "Wildboy of Wideboy + 500 AW (if AL = 15)",
        "Stats": {"AttackWidth": 500},
        "Condition": lambda stats: stats["Attacklength"] == 15  
    },
    {
        "Name": "Wildboy of Long + 200 AL (if AW = 15)",
        "Stats": {"AttackLength": 200},
        "Condition": lambda stats: stats["AttackWidth"] == 15  
    },
    {
        "Name": "Wildboy of Risk + 50 AD (if AL < 30)",
        "Stats": {"AttackDamage": 50},
        "Condition": lambda stats: stats["AttackLength"] < 30 
    },
    {
        "Name": "Wildboy of Dashydashy +.9 DC (if A = 0)",
        "Stats": {"DashCooldown": -0.9},
        "Condition": lambda stats: stats["Armor"] == 0  
    },
    {
        "Name": "Wildboy of Pancake + 200 AL & AW (if H < 25) ",
        "Stats": {"AttackLength": 200, "AttackWidth": 200},
        "Condition": lambda stats: stats["Health"] < 25 
    },
    {
        "Name": "Wildboy of Sloth + 20 AD + 5 A (if AS < .8)",
        "Stats": {"AttackDamage": 20, "Armor": 5},
        "Condition": lambda stats: stats["AttackSpeed"] < 0.8  # Boost if DashCooldown < 2
    },
]


# Player stats initialized as a copy of the default stats
player_stats = DEFAULT_PLAYER_STATS.copy()

# Player inventory
inventory = {
    "Weapons": [],
    "Armor": []
}
equipment = {
    "Weapons": [],
    "Armor": [],
    "Wildboys": []
}

# Generate a tier 1 weapon and equip it at the start of the game
def initialize_player_with_weapon():
    global inventory, equipment
    tier = 0  # Starting with a tier 1 weapon
    weapon = generate_equipment(tier, "Weapon")  # Generate a tier 1 weapon
    equipment["Weapons"].append(weapon)  # Equip the weapon

# Call this function after initializing the player's stats
initialize_player_with_weapon()

# DASH FEATURE: Initialize dash-related variables
dashing = False
dash_start_time = 0
last_dash_time = 0
dash_invuln_duration = 0.2  # Duration of invulnerability in seconds during dash
# Variables for incremental dash movement
dash_direction = pygame.math.Vector2(0, 0)  # Direction vector for the dash
dash_distance_remaining = 0
dash_speed = 2000  # Pixels per second; adjust as needed for dash speed


# Attack parameters
final_stats = calculate_final_stats()
attack_cooldown = 1.0 / final_stats["AttackSpeed"]
last_attack_time = 0
sword_hitbox = None  # Will store the sword rect when attacking

# Room parameters
ROOM_WIDTH, ROOM_HEIGHT = 800, 600
WALL_THICKNESS = 20
EXIT_WIDTH = 100
EXIT_HEIGHT = 20

player_size = 20
player_rect = pygame.Rect(0, 0, player_size, player_size)

walls = []
room_id = 0

enemies = []


# Damage timing
damage_cooldown = 0.5
last_damage_time = time.time()

game_over = False
font = pygame.font.SysFont(None, 48)

def draw_stats(surface, stats, font, x, y):
    """Draw player stats at the specified (x, y) position."""
    spacing = 20  # Space between lines
    for i, (key, value) in enumerate(stats.items()):
        stat_text = f"{key}: {value}"
        text_surface = font.render(stat_text, True, (255, 255, 255))  # White text
        surface.blit(text_surface, (x, y + i * spacing))

def get_tier(room_id):
    if room_id < 10:  # Tier 1 (Rooms 1–9)
        return 1
    return ((room_id - 1) // 10) + 1  # Tiers 2+ (Rooms 10–19, 20–29, etc.)

def get_enemy_ranges_for_tier(tier):
    capped_tier = min(tier, 10)
    
    health_ranges = [(10,20),(20,30),(30,40),(40,50),(50,60),(60,70),(70,80),(80,90),(90,100),(100,120)]
    speed_ranges = [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(9,10),(10,12)]
    damage_ranges = [(5,10),(10,15),(15,20),(20,25),(25,30),(30,35),(35,40),(40,45),(45,50),(50,60)]
    size_ranges = [(20,30),(25,35),(30,40),(35,45),(40,50),(45,55),(50,60),(55,65),(60,70),(65,75)]
    enemy_behavior_ranges = [(0,1),(0,1),(1,2),(1,2),(2,3),(2,3),(3,4),(3,4),(4,5),(4,5)]
    enemy_count_ranges = [(2,4),(3,5),(4,6),(5,7),(6,8),(7,9),(8,10),(9,11),(10,12),(12,15)]
    
    return {
        "health": health_ranges[capped_tier-1],
        "speed": speed_ranges[capped_tier-1],
        "damage": damage_ranges[capped_tier-1],
        "size": size_ranges[capped_tier-1],
        "behavior": enemy_behavior_ranges[capped_tier-1],
        "count": enemy_count_ranges[capped_tier-1]
    }

def spawn_enemies(tier):
    global enemies
    enemies = []
    ranges = get_enemy_ranges_for_tier(tier)
    num_enemies = random.randint(*ranges["count"])
    
    for _ in range(num_enemies):
        placed = False
        attempts = 0
        while not placed and attempts < 100:
            enemy_x = random.randint((WIDTH - ROOM_WIDTH)//2 + WALL_THICKNESS + 30,
                                     (WIDTH + ROOM_WIDTH)//2 - WALL_THICKNESS - 30)
            enemy_y = random.randint((HEIGHT - ROOM_HEIGHT)//2 + WALL_THICKNESS + 30,
                                     (HEIGHT + ROOM_HEIGHT)//2 - WALL_THICKNESS - 30)
            new_rect = pygame.Rect(enemy_x, enemy_y, 10, 10) # temporary, will resize
            
            if not any(new_rect.colliderect(w) for w in walls):
                health = random.randint(*ranges["health"])
                speed = random.uniform(*ranges["speed"])
                damage = random.randint(*ranges["damage"])
                enemy_behavior = random.uniform(*ranges["behavior"])
                size_val = random.randint(*ranges["size"])
                new_rect.width = size_val
                new_rect.height = size_val
                if not any(new_rect.colliderect(e["rect"]) for e in enemies):
                    enemies.append({
                        "rect": new_rect,
                        "health": health,
                        "max_health": health,  # Track the maximum health
                        "speed": speed,
                        "damage": damage,
                        "behavior": enemy_behavior,
                        "weapon": {  # Add randomized weapon stats
                            "attack_damage": random.randint(5, 15) * get_tier(room_id),
                            "attack_speed": random.uniform(0.5, 1.5),
                            "attack_size": random.uniform(1.0, 2.0)
                        },
                        "last_attack_time": 0  # Cooldown timer for the enemy's weapon attacks
                    })
                    placed = True
            attempts += 1

def spawn_boss(tier):
    """
    Spawns a boss enemy with stats 4x the normal range of the given tier.
    """
    global enemies
    ranges = get_enemy_ranges_for_tier(tier)
    
    enemy_behavior = random.uniform(*ranges["behavior"])
    
    boss = {
        "rect": pygame.Rect(WIDTH // 2 - 30, HEIGHT // 2 - 30, 60, 60),  # Larger boss size
        "health": random.randint(ranges["health"][0] * 4, ranges["health"][1] * 4),
        "max_health": random.randint(ranges["health"][0] * 4, ranges["health"][1] * 4),
        "speed": random.uniform(ranges["speed"][0] * 1, ranges["speed"][1] * 1),  # Bosses are slower
        "damage": random.randint(ranges["damage"][0] * 4, ranges["damage"][1] * 4),
        "behavior": enemy_behavior,
        "weapon": {
            "attack_damage": random.randint(15, 30) * tier,
            "attack_speed": random.uniform(0.5, 1.0),  # Slower attacks
            "attack_size": random.uniform(2.0, 4.0)  # Larger attack range
        },
        "last_attack_time": 0,  # Initialize attack timer
    }
    enemies.append(boss)


def create_room():
    w = []
    left_wall = pygame.Rect((WIDTH - ROOM_WIDTH)//2, (HEIGHT - ROOM_HEIGHT)//2, WALL_THICKNESS, ROOM_HEIGHT)
    right_wall = pygame.Rect((WIDTH + ROOM_WIDTH)//2 - WALL_THICKNESS, (HEIGHT - ROOM_HEIGHT)//2, WALL_THICKNESS, ROOM_HEIGHT)
    top_wall = pygame.Rect((WIDTH - ROOM_WIDTH)//2, (HEIGHT - ROOM_HEIGHT)//2, ROOM_WIDTH, WALL_THICKNESS)
    bottom_wall = pygame.Rect((WIDTH - ROOM_WIDTH)//2, (HEIGHT + ROOM_HEIGHT)//2 - WALL_THICKNESS, ROOM_WIDTH, WALL_THICKNESS)
    w.extend([left_wall, right_wall, top_wall, bottom_wall])
    
    exit_x = (WIDTH - EXIT_WIDTH)//2
    exit_y = (HEIGHT - ROOM_HEIGHT)//2
    w.remove(top_wall)
    if exit_x > top_wall.x:
        top_wall_left = pygame.Rect(top_wall.x, top_wall.y, exit_x - top_wall.x, WALL_THICKNESS)
        top_wall_right = pygame.Rect(exit_x + EXIT_WIDTH, top_wall.y, (top_wall.x + ROOM_WIDTH) - (exit_x + EXIT_WIDTH), WALL_THICKNESS)
        w.append(top_wall_left)
        w.append(top_wall_right)
    
    corridor_left = (WIDTH // 2) - 50
    corridor_right = (WIDTH // 2) + 50
    
    for _ in range(5):
        obs_width = random.randint(40, 80)
        obs_height = random.randint(40, 80)
        
        placed = False
        attempts = 0
        while not placed and attempts < 50:
            obs_x = random.randint((WIDTH - ROOM_WIDTH)//2 + WALL_THICKNESS, (WIDTH + ROOM_WIDTH)//2 - WALL_THICKNESS - obs_width)
            obs_y = random.randint((HEIGHT - ROOM_HEIGHT)//2 + WALL_THICKNESS + 50, (HEIGHT + ROOM_HEIGHT)//2 - WALL_THICKNESS - obs_height - 50)
            
            if obs_x < corridor_left - obs_width or obs_x > corridor_right:
                new_obs = pygame.Rect(obs_x, obs_y, obs_width, obs_height)
                if not any(new_obs.colliderect(x) for x in w):
                    w.append(new_obs)
                    placed = True
            attempts += 1
    
    return w


def new_room():
    global walls, room_id, chest_rect, chest_spawned, chest_opened, COLOR_BG, COLOR_WALL, health_fountain_rect, fountain_spawned, fountain_used, fountain_should_spawn, levelgate_rect, levelgate_spawned, levelgate_used, levelgate_should_spawn

    # Reset room elements
    walls = create_room()
    room_id += 1
    tier = get_tier(room_id)
    chest_rect = None
    chest_spawned = False
    chest_opened = False

    # Reset health fountain for non-boss rooms
    if room_id % 10 != 0:  # Not a boss room
        health_fountain_rect = None
        fountain_spawned = False
        fountain_used = False  # Reset fountain state
        levelgate_rect = None
        levelgate_spawned = False
        levelgate_used = False  # Reset fountain state
    elif room_id % 10 == 0 and fountain_should_spawn:  # Boss room and fountain allowed
        health_fountain_rect = pygame.Rect(WIDTH // 2 - 20, (HEIGHT // 2 + ROOM_HEIGHT // 4) - 20, 40, 40)
        fountain_spawned = True
        fountain_used = False  # Reset fountain state for the new boss room
    elif room_id % 10 == 0 and levelgate_should_spawn:  # Boss room and fountain allowed
        levelgate_rect = pygame.Rect(
            (WIDTH - EXIT_WIDTH) // 2,  # Position level gate to align with the horizontal exit
            (HEIGHT - ROOM_HEIGHT) // 2,  # Position level gate at the top exit area
            EXIT_WIDTH,
            WALL_THICKNESS  # Same thickness as the wall
        )
        levelgate_spawned = True
        levelgate_used = False  # Reset fountain state
        
    # Spawn enemies
    if room_id % 10 == 0:  # Check if this is the 10th room (boss room)
        spawn_boss(tier)
    else:
        spawn_enemies(tier)

    # Update room colors based on tier
    colors = get_room_colors(tier)
    COLOR_BG = colors["bg"]
    COLOR_WALL = colors["wall"]

def show_level_up_screen():
    """
    Displays the level-up screen where the player can pick a 'wildboy' or exit.
    Includes a stats box positioned higher to ensure visibility of all text.
    """
    running_level_up = True
    font_title = pygame.font.SysFont(None, 64)
    font_subtitle = pygame.font.SysFont(None, 36)
    font_option = pygame.font.SysFont(None, 48)
    font_stats = pygame.font.SysFont(None, 24)  # Smaller font for stats

    # Colors and layout
    bg_color = (50, 50, 100)
    text_color = (255, 255, 255)
    hover_color = (200, 200, 0)
    box_color = (30, 30, 60)
    border_color = (255, 255, 255)

    # Select three random Wildboys
    selected_wildboys = select_random_wildboys()
    options = [wildboy["Name"] for wildboy in selected_wildboys] + ["Exit"]

    # Adjusted stats box position and size
    stats_box_width = 250
    stats_box_height = 200
    stats_box_x = 20
    stats_box_y = HEIGHT - stats_box_height - 60

    while running_level_up:
        WIN.fill(bg_color)

        # Draw title
        title_text = font_title.render("LEVEL UP!", True, text_color)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 100))
        WIN.blit(title_text, title_rect)

        # Draw subtitle
        subtitle_text = font_subtitle.render("Pick a wildboy (permanent stat boost):", True, text_color)
        subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, 160))
        WIN.blit(subtitle_text, subtitle_rect)

        # Draw options and handle hover effects
        mx, my = pygame.mouse.get_pos()
        option_rects = []

        for i, option in enumerate(options):
            option_text = font_option.render(option, True, text_color)
            option_rect = option_text.get_rect(center=(WIDTH // 2, 220 + i * 60))
            option_rects.append(option_rect)
            WIN.blit(option_text, option_rect)

            # Highlight on hover
            if option_rect.collidepoint(mx, my):
                pygame.draw.rect(WIN, hover_color, option_rect.inflate(10, 10), border_radius=5)
                WIN.blit(font_option.render(option, True, bg_color), option_rect)

        # Draw stats box higher to show all stats
        pygame.draw.rect(WIN, box_color, (stats_box_x, stats_box_y, stats_box_width, stats_box_height))
        pygame.draw.rect(WIN, border_color, (stats_box_x, stats_box_y, stats_box_width, stats_box_height), 2)

        stats_title = font_subtitle.render("Player Stats", True, text_color)
        WIN.blit(stats_title, (stats_box_x + 10, stats_box_y + 10))

        # Align stats text neatly inside the box
        line_spacing = 20
        max_stats_lines = (stats_box_height - 40) // line_spacing  # Max number of lines that fit
        for i, (stat_name, stat_value) in enumerate(player_stats.items()):
            if i >= max_stats_lines:
                break  # Stop if exceeding the box height
            stat_text = font_stats.render(f"{stat_name}: {stat_value}", True, text_color)
            WIN.blit(stat_text, (stats_box_x + 10, stats_box_y + 40 + i * line_spacing))

        pygame.display.flip()

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    for i, rect in enumerate(option_rects):
                        if rect.collidepoint(mx, my):
                            if options[i] == "Exit":
                                running_level_up = False  # Exit the level-up screen
                            else:
                                # Add the selected Wildboy to equipment
                                selected_wildboy = selected_wildboys[i]
                                equipment["Wildboys"].append(selected_wildboy)
                                print(f"You selected {selected_wildboy['Name']}!")  # Debug output
                                running_level_up = False  # Exit after selection


def reset_game():
    global player_stats, room_id, walls, enemies, player_rect, game_over, last_damage_time, last_attack_time, inventory, equipment, chest_spawned, chest_opened, chest_item, fountain_spawned, fountain_used, levelgate_spawned, levelgate_used, levelgate_rect, health_fountain_rect

    # Reset player stats to default
    player_stats = DEFAULT_PLAYER_STATS.copy()
    
    # Reset inventory and equipment
    inventory = {
        "Weapons": [],
        "Armor": []
    }
    equipment = {
        "Weapons": [],
        "Armor": []
    }
    
    # Equip starter weapon
    initialize_player_with_weapon()

    # Reset room state
    room_id = 0
    walls = []
    enemies = []
    chest_spawned = False
    chest_opened = False
    chest_item = None
    health_fountain_rect = None
    fountain_spawned = False
    fountain_used = False
    levelgate_rect = None
    levelgate_spawned = False
    levelgate_used = False

    # Reset game state variables
    game_over = False
    last_damage_time = time.time()
    last_attack_time = 0

    # Generate the first room
    new_room()
    
    # Place player in the starting position
    player_rect.centerx = WIDTH // 2
    player_rect.bottom = (HEIGHT + ROOM_HEIGHT) // 2 - WALL_THICKNESS - 10

# Initial room
new_room()
player_rect.centerx = WIDTH//2
player_rect.bottom = (HEIGHT + ROOM_HEIGHT)//2 - WALL_THICKNESS - 10

clock = pygame.time.Clock()
running = True
show_inventory = False  # Track inventory display state

while running:
    dt = clock.tick(60) / 1000.0
    current_time = time.time()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
        # Toggle inventory display on 'F' key press
        if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            show_inventory = not show_inventory
            
        # Handle mouse click for inventory interaction
        if event.type == pygame.MOUSEBUTTONDOWN and show_inventory:
            if event.button == 1:  # Left click
                mx, my = pygame.mouse.get_pos()
                handle_inventory_click(mx, my)
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            final_stats = calculate_final_stats()  # Ensure final stats are up to date
            if current_time > last_dash_time + final_stats["DashCooldown"]:
                # DASH FEATURE: Initiate dash
                # Determine dash direction from the player's last movement input
                dash_dir = pygame.math.Vector2(0, 0)
                if keys[pygame.K_w]:
                    dash_dir.y -= 1
                if keys[pygame.K_s]:
                    dash_dir.y += 1
                if keys[pygame.K_a]:
                    dash_dir.x -= 1
                if keys[pygame.K_d]:
                    dash_dir.x += 1
                
                # If no direction keys were pressed, default dash direction upward
                if dash_dir.length() == 0:
                    dash_dir.y = -1
                
                dash_dir = dash_dir.normalize()
                
                # Set dash variables for incremental movement
                dashing = True
                dash_direction = dash_dir
                dash_distance_remaining = final_stats["DashDistance"]
                dash_start_time = current_time
                last_dash_time = current_time                
   
    if game_over:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            reset_game()
        # Draw Game Over Screen
        WIN.fill(COLOR_BG)
        game_over_text = font.render("Game Over! Press R to Restart", True, COLOR_GAME_OVER)
        rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        WIN.blit(game_over_text, rect)
        pygame.display.flip()
        continue
   

  
    def render_wrapped_text(surface, text, font, color, x, y, max_width):
        words = text.split(' ')
        line = ""
        height = y
        for word in words:
            test_line = line + word + " "
            if font.size(test_line)[0] > max_width:
                render = font.render(line, True, color)
                surface.blit(render, (x, height))
                height += font.get_linesize()
                line = word + " "
            else:
                line = test_line
        if line:
            render = font.render(line, True, color)
            surface.blit(render, (x, height))
    
    def handle_inventory_click(mx, my):
        global inventory, equipment

        inventory_x = 20
        inventory_y = 20
        inventory_width = WIDTH // 2 - 40
        inventory_height = HEIGHT - 40
        max_items = 3
        weapon_spacing = (inventory_height // 2 - 60) // max_items
        armor_spacing = (inventory_height // 2 - 60) // max_items
        delete_mode = pygame.key.get_pressed()[pygame.K_LSHIFT]  # Check if Shift key is held
        
        # Detect clicks on Weapons in Inventory
        # Use the same rect as in the drawing code
        for i, weapon in enumerate(inventory["Weapons"]):
            weapon_rect = pygame.Rect(inventory_x + 10, inventory_y + 80 + i * weapon_spacing, inventory_width - 20, weapon_spacing - 10)
            if weapon_rect.collidepoint(mx, my):
                if delete_mode:
                    # Delete weapon permanently
                    print(f"Deleting {weapon['Name']} from inventory.")
                    inventory["Weapons"].remove(weapon)
                else:
                    # Equip weapon
                    if weapon in inventory["Weapons"]:
                        if equipment["Weapons"]:
                            unequipped = equipment["Weapons"].pop()
                            inventory["Weapons"].append(unequipped)
                        inventory["Weapons"].remove(weapon)
                        equipment["Weapons"].append(weapon)
                return

        # Detect clicks on Armor in Inventory
        # Use the same rect as in the drawing code
        inventory_armor_start_y = inventory_y + inventory_height // 2 + 30
        for i, armor in enumerate(inventory["Armor"]):
            armor_rect = pygame.Rect(inventory_x + 10, inventory_armor_start_y + 30 + i * armor_spacing, inventory_width - 20, armor_spacing - 10)
            if armor_rect.collidepoint(mx, my):
                if delete_mode:
                    # Delete armor permanently
                    print(f"Deleting {armor['Name']} from inventory.")
                    inventory["Armor"].remove(armor)
                else:
                    # Equip armor
                    if armor in inventory["Armor"]:
                        if equipment["Armor"]:
                            unequipped = equipment["Armor"].pop()
                            inventory["Armor"].append(unequipped)
                        inventory["Armor"].remove(armor)
                        equipment["Armor"].append(armor)
                return

        # Detect clicks on Equipped Weapon
        equipped_weapon_x = WIDTH // 2 + 30
        equipped_weapon_y = 80
        if equipment["Weapons"]:
            equipped_weapon_rect = pygame.Rect(equipped_weapon_x, equipped_weapon_y, inventory_width - 20, 30)
            if equipped_weapon_rect.collidepoint(mx, my):
                # Unequip the weapon and add it back to inventory
                unequipped_weapon = equipment["Weapons"].pop()
                add_to_inventory(unequipped_weapon, "Weapons")
                return

        # Detect clicks on Equipped Armor
        equipped_armor_y = (HEIGHT - 80) // 2 + 70
        if equipment["Armor"]:
            equipped_armor_rect = pygame.Rect(equipped_weapon_x, equipped_armor_y, inventory_width - 20, 30)
            if equipped_armor_rect.collidepoint(mx, my):
                # Unequip the armor and add it back to inventory
                unequipped_armor = equipment["Armor"].pop()
                add_to_inventory(unequipped_armor, "Armor")
                return
                
    if show_inventory:
        WIN.fill(COLOR_BG)  # Clear screen
        font_title = pygame.font.SysFont(None, 36)
        font_item = pygame.font.SysFont(None, 24)
        delete_mode = pygame.key.get_pressed()[pygame.K_LSHIFT]  # Check if Shift key is held

        # Left Side: Inventory
        inventory_x = 20
        inventory_y = 20
        inventory_width = WIDTH // 2 - 40
        inventory_height = HEIGHT - 40
        pygame.draw.rect(WIN, (50, 50, 50), (inventory_x, inventory_y, inventory_width, inventory_height))

        # Inventory Title
        inventory_title = font_title.render("Inventory", True, (255, 255, 255))
        WIN.blit(inventory_title, (inventory_x + 10, inventory_y + 10))

        # Calculate dynamic spacing for items
        max_items = 3  # Maximum number of weapons/armor
        weapon_spacing = (inventory_height // 2 - 60) // max_items
        armor_spacing = (inventory_height // 2 - 60) // max_items

        # Display Weapons in Inventory
        inventory_weapons_title = font_title.render("Weapons", True, (200, 200, 200))
        WIN.blit(inventory_weapons_title, (inventory_x + 10, inventory_y + 50))
        for i, weapon in enumerate(inventory["Weapons"]):
            weapon_rect = pygame.Rect(inventory_x + 10, inventory_y + 80 + i * weapon_spacing, inventory_width - 20, weapon_spacing - 10)
            weapon_color = (255, 0, 0) if delete_mode else (200, 200, 200)  # Red background in delete mode
            pygame.draw.rect(WIN, weapon_color, weapon_rect)
            weapon_text = f"{weapon['Name']} - Stats: {weapon['Stats']}"
            render_wrapped_text(WIN, weapon_text, font_item, (0, 0, 0), weapon_rect.x + 5, weapon_rect.y + 5, weapon_rect.width - 10)

        # Display Armor in Inventory
        inventory_armor_title = font_title.render("Armor", True, (200, 200, 200))
        inventory_armor_start_y = inventory_y + inventory_height // 2 + 30
        WIN.blit(inventory_armor_title, (inventory_x + 10, inventory_armor_start_y))
        for i, armor in enumerate(inventory["Armor"]):
            armor_rect = pygame.Rect(inventory_x + 10, inventory_armor_start_y + 30 + i * armor_spacing, inventory_width - 20, armor_spacing - 10)
            armor_color = (255, 0, 0) if delete_mode else (200, 200, 200)  # Red background in delete mode
            pygame.draw.rect(WIN, armor_color, armor_rect)
            armor_text = f"{armor['Name']} - Stats: {armor['Stats']}"
            render_wrapped_text(WIN, armor_text, font_item, (0, 0, 0), armor_rect.x + 5, armor_rect.y + 5, armor_rect.width - 10)

        # Right Side: Equipment
        equipment_x = WIDTH // 2 + 20
        equipment_y = 20
        equipment_width = WIDTH // 2 - 40
        equipment_height = inventory_height
        pygame.draw.rect(WIN, (50, 50, 50), (equipment_x, equipment_y, equipment_width, equipment_height))

        # Equipment Title
        equipment_title = font_title.render("Equipment", True, (255, 255, 255))
        WIN.blit(equipment_title, (equipment_x + 10, equipment_y + 10))

        # Define consistent spacing between sections
        section_spacing = 100  # Spacing between equipment sections

        # Display Weapon Slot
        weapon_slot_title = font_title.render("Weapon", True, (200, 200, 200))
        weapon_slot_y = equipment_y + 50
        WIN.blit(weapon_slot_title, (equipment_x + 10, weapon_slot_y))
        if equipment["Weapons"]:
            equipped_weapon = equipment["Weapons"][0]
            weapon_text = f"{equipped_weapon['Name']} - Stats: {equipped_weapon['Stats']}"
            render_wrapped_text(WIN, weapon_text, font_item, (200, 200, 200), equipment_x + 10, weapon_slot_y + 30, equipment_width - 20)
        else:
            empty_weapon_text = font_item.render("None", True, (100, 100, 100))
            WIN.blit(empty_weapon_text, (equipment_x + 10, weapon_slot_y + 30))

        # Display Armor Slot
        armor_slot_title = font_title.render("Armor", True, (200, 200, 200))
        armor_slot_y = weapon_slot_y + section_spacing
        WIN.blit(armor_slot_title, (equipment_x + 10, armor_slot_y))
        if equipment["Armor"]:
            equipped_armor = equipment["Armor"][0]
            armor_text = f"{equipped_armor['Name']} - Stats: {equipped_armor['Stats']}"
            render_wrapped_text(WIN, armor_text, font_item, (200, 200, 200), equipment_x + 10, armor_slot_y + 30, equipment_width - 20)
        else:
            empty_armor_text = font_item.render("None", True, (100, 100, 100))
            WIN.blit(empty_armor_text, (equipment_x + 10, armor_slot_y + 30))

        # Display Wildboys Slot
        wildboys_slot_title = font_title.render("Wildboys", True, (200, 200, 200))
        wildboys_slot_y = armor_slot_y + section_spacing
        WIN.blit(wildboys_slot_title, (equipment_x + 10, wildboys_slot_y))
        if equipment["Wildboys"]:
            wildboy_spacing = 30  # Spacing between Wildboy entries
            for i, wildboy in enumerate(equipment["Wildboys"]):
                wildboy_text = f"{wildboy['Name']}"
                render_wrapped_text(WIN, wildboy_text, font_item, (200, 200, 200),
                                    equipment_x + 10,
                                    wildboys_slot_y + 30 + i * wildboy_spacing,
                                    equipment_width - 20)
        else:
            empty_wildboys_text = font_item.render("None", True, (100, 100, 100))
            WIN.blit(empty_wildboys_text, (equipment_x + 10, wildboys_slot_y + 30))
        
        pygame.display.flip()
        continue

    # Player input
    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()
    mx, my = pygame.mouse.get_pos()
    final_stats = calculate_final_stats()
    move_speed = final_stats["MovementSpeed"]
    dx = dy = 0
    if keys[pygame.K_w]:
        dy = -move_speed
    if keys[pygame.K_s]:
        dy = move_speed
    if keys[pygame.K_a]:
        dx = -move_speed
    if keys[pygame.K_d]:
        dx = move_speed
    
    # Move player (no enemy collision check)
    def can_move(rect, x_off, y_off):
        test_rect = rect.copy()
        test_rect.x += x_off
        test_rect.y += y_off
        if any(test_rect.colliderect(w) for w in walls):
            return False
        return True
    
    if can_move(player_rect, dx, 0):
        player_rect.x += dx
    if can_move(player_rect, 0, dy):
        player_rect.y += dy
    
    # Handle incremental dash movement
    if dashing:
        # Calculate movement for this frame
        movement = dash_direction * dash_speed * dt
        movement_length = movement.length()

        # Ensure we don't overshoot the remaining dash distance
        if movement_length > dash_distance_remaining:
            movement = dash_direction * dash_distance_remaining
            movement_length = dash_distance_remaining

        # Attempt to move horizontally
        if movement.x != 0:
            player_rect.x += int(movement.x)
            if any(player_rect.colliderect(w) for w in walls):
                # Collision detected, revert horizontal movement
                player_rect.x -= int(movement.x)
                dashing = False
                dash_distance_remaining = 0
            else:
                dash_distance_remaining -= abs(movement.x)

        # Attempt to move vertically
        if movement.y != 0 and dashing:
            player_rect.y += int(movement.y)
            if any(player_rect.colliderect(w) for w in walls):
                # Collision detected, revert vertical movement
                player_rect.y -= int(movement.y)
                dashing = False
                dash_distance_remaining = 0
            else:
                dash_distance_remaining -= abs(movement.y)

        # Check if dash is complete
        if dash_distance_remaining <= 0:
            dashing = False
    
    # Check if player opens the chest
    if chest_rect and player_rect.colliderect(chest_rect):
        if keys[pygame.K_e] and not chest_interacted:  # Only interact if key is newly pressed
            # Only proceed if the chest has not already been resolved
            if not chest_opened:
                # Generate an item if the chest is empty
                if chest_item is None:
                    tier = get_tier(room_id)
                    equipment_type = random.choice(["Weapon", "Armor"])  # Randomly pick type
                    chest_item = generate_equipment(tier, equipment_type)
                    print(f"A {chest_item['Name']} has appeared in the chest!")  # Debug log

                # Determine item type based on stats
                equipment_type = "Weapons" if "AttackDamage" in chest_item["Stats"] else "Armor"

                # Check if inventory has space
                if (equipment_type == "Weapons" and len(inventory["Weapons"]) < 3) or (
                    equipment_type == "Armor" and len(inventory["Armor"]) < 3
                ):
                    add_to_inventory(chest_item, equipment_type)
                    print(f"You took the {chest_item['Name']} from the chest!")  # Notify player
                    chest_item = None  # Clear the chest item
                    chest_opened = True  # Mark chest as resolved
                else:
                    print(f"Your inventory is full! The {chest_item['Name']} remains in the chest.")
            else:
                print("The chest is empty or already opened.")  # Chest is resolved

            chest_interacted = True  # Mark the interaction as handled
        elif not keys[pygame.K_e]:  # Reset the flag when the key is released
            chest_interacted = False    
    
    # Check if player interacts with the health fountain
    if health_fountain_rect and player_rect.colliderect(health_fountain_rect) and not fountain_used:
        if keys[pygame.K_e]:  # Interact with the fountain
            final_stats = calculate_final_stats()  # Update player stats
            player_stats["Health"] = final_stats["MaxHealth"]  # Fully restore health
            fountain_used = True
            fountain_should_spawn = False  # Disable spawning until the next boss room
            print("You have restored your health!")  # Debug message
            
        # Check if player interacts with the levelgate and then spawn levelup screen
    if levelgate_rect and player_rect.colliderect(levelgate_rect) and not levelgate_used:
            levelgate_used = True
            levelgate_should_spawn = False  # Disable spawning until the next boss room
            show_level_up_screen()
            print("You have touched the level gate")  # Debug message
    
    # Enemy movement (only blocked by walls)
    for e in enemies:
        ex, ey = e["rect"].center
        px, py = player_rect.center
        dir_x = px - ex
        dir_y = py - ey
        dist = (dir_x**2 + dir_y**2)**0.5
        if dist != 0:
            dir_x /= dist
            dir_y /= dist
    
        erratic_x = random.uniform(-e["behavior"], e["behavior"])
        erratic_y = random.uniform(-e["behavior"], e["behavior"])
        dir_x += erratic_x
        dir_y += erratic_y
        dist2 = (dir_x**2 + dir_y**2)**0.5
        if dist2 != 0:
            dir_x /= dist2
            dir_y /= dist2
    
        old_pos = e["rect"].topleft
        e["rect"].x += int(dir_x * e["speed"])
        e["rect"].y += int(dir_y * e["speed"])
    
        if any(e["rect"].colliderect(w) for w in walls):
            e["rect"].topleft = old_pos

        # Enemy sword attack logic
        time_since_last_attack = current_time - e["last_attack_time"]

        # Calculate distance to player
        ex, ey = e["rect"].center
        px, py = player_rect.center
        distance_to_player = math.hypot(px - ex, py - ey)

        # Check if player is close enough to be attacked
        attack_range = 50 * e["weapon"]["attack_size"]  # Modify attack range based on weapon size

        if distance_to_player <= attack_range and time_since_last_attack >= (1 / e["weapon"]["attack_speed"]):
            # Determine attack direction
            dir_x = px - ex
            dir_y = py - ey

            # Calculate direction: right, left, up, or down
            if abs(dir_x) > abs(dir_y):  # Horizontal swing
                if dir_x > 0:
                    direction = "right"
                else:
                    direction = "left"
            else:  # Vertical swing
                if dir_y > 0:
                    direction = "down"
                else:
                    direction = "up"

            # Create sword hitbox
            sword_length = 20 * e["weapon"]["attack_size"]
            sword_width = 10 * e["weapon"]["attack_size"]
            enemy_sword_rect = pygame.Rect(0, 0, sword_length, sword_width)

            # Position sword hitbox based on direction
            if direction == "right":
                enemy_sword_rect.midleft = e["rect"].midright
            elif direction == "left":
                enemy_sword_rect.midright = e["rect"].midleft
            elif direction == "up":
                enemy_sword_rect.width, enemy_sword_rect.height = sword_width, sword_length
                enemy_sword_rect.midbottom = e["rect"].midtop
            elif direction == "down":
                enemy_sword_rect.width, enemy_sword_rect.height = sword_width, sword_length
                enemy_sword_rect.midtop = e["rect"].midbottom

            # Store the sword rect and duration for the swing animation
            e["sword_rect"] = enemy_sword_rect
            e["swing_end_time"] = current_time + 0.2

            # Check for collision with the player
            if enemy_sword_rect.colliderect(player_rect):
                if not (dashing and (current_time - dash_start_time < dash_invuln_duration)):
                    # Apply damage only if the player is not invulnerable
                    final_stats = calculate_final_stats(damage=e["weapon"]["attack_damage"])

            # Update attack cooldown
            e["last_attack_time"] = current_time
    
    # Player Attack
    # Determine direction from mouse position relative to player
    px, py = player_rect.center
    angle = math.degrees(math.atan2(my - py, mx - px))
    # Normalize angle to [0, 360)
    angle = angle % 360
    
    # If mouse button is held and cooldown passed, attack
    if mouse_buttons[0]: # left mouse button
        final_stats = calculate_final_stats()
        attack_cooldown = 1.0 / final_stats["AttackSpeed"]
        if current_time > last_attack_time + attack_cooldown:
            # Attack
            # Determine direction: up, down, left, right
            # We'll pick the major direction based on angle:
            # Right: -45 to 45 degrees
            # Down: 45 to 135 degrees
            # Left: 135 to 225 degrees
            # Up: 225 to 315 degrees
            # (Or you could use if statements to categorize)
            if (angle >= 315 or angle < 45):
                # right
                direction = "right"
            elif 45 <= angle < 135:
                direction = "down"
            elif 135 <= angle < 225:
                direction = "left"
            else:
                direction = "up"
            
            final_stats = calculate_final_stats()
            sword_length = final_stats["AttackLength"]
            sword_width = final_stats["AttackWidth"]
            
            # Position sword relative to player based on direction
            sword_rect = pygame.Rect(0, 0, sword_length, sword_width)
            if direction == "right":
                sword_rect.midleft = (player_rect.right, player_rect.centery)
            elif direction == "left":
                sword_rect.midright = (player_rect.left, player_rect.centery)
            elif direction == "up":
                # rotate dimensions so length is vertical
                sword_rect.width, sword_rect.height = sword_width, sword_length
                sword_rect.midbottom = (player_rect.centerx, player_rect.top)
            elif direction == "down":
                sword_rect.width, sword_rect.height = sword_width, sword_length
                sword_rect.midtop = (player_rect.centerx, player_rect.bottom)
            
            # Check for enemy hits
            for e in enemies:
                if e["rect"].colliderect(sword_rect):
                    final_stats = calculate_final_stats()
                    e["health"] -= final_stats["AttackDamage"]
        
           
            last_attack_time = current_time
            sword_hitbox = sword_rect.copy()
        else:
            # currently on cooldown, no new attack
            sword_hitbox = None
    else:
        sword_hitbox = None

    # Damage application with Armor reduction (minimum 1 damage)
    if dashing and (current_time - dash_start_time < dash_invuln_duration):
        # Skip damage while dashing
        touching_enemies = []
    else:
        touching_enemies = [en for en in enemies if en["rect"].colliderect(player_rect)]
        if touching_enemies and current_time > last_damage_time + damage_cooldown:
            # Calculate the total damage from all touching enemies
            total_damage = sum(en["damage"] for en in touching_enemies)

            # Update player stats with the calculated damage
            final_stats = calculate_final_stats(damage=total_damage)

            # Update last damage time to enforce cooldown
            last_damage_time = current_time
        
    # If player is dashing and within invuln window, skip damage:
    if dashing and (current_time - dash_start_time < dash_invuln_duration):
        # Skip damage while dashing
        touching_enemies = []

    # Update enemy list to remove dead enemies
    enemies = [en for en in enemies if en["health"] > 0]

    # Check if all enemies are dead and spawn the chest/health fountain if not already spawned
    if not enemies and not chest_spawned:
        chest_rect = pygame.Rect(WIDTH // 2 - 20, HEIGHT // 2 - 20, 40, 40)  # Spawn chest in the center
        chest_spawned = True
        
        # Spawn health fountain only in boss rooms (final room of each tier)
        if room_id % 10 == 0 and not fountain_spawned:
            health_fountain_rect = pygame.Rect(WIDTH // 2 - 20, (HEIGHT // 2 + ROOM_HEIGHT // 4) - 20, 40, 40)
            fountain_spawned = True
            fountain_used = False
        else:
            health_fountain_rect = None  # Remove the fountain from other rooms
        
        # Spawn levelgate only in boss rooms (final room of each tier)
        if room_id % 10 == 0 and not levelgate_spawned:
            levelgate_rect = pygame.Rect(
                (WIDTH - EXIT_WIDTH) // 2,  # Position level gate to align with the horizontal exit
                (HEIGHT - ROOM_HEIGHT) // 2,  # Position level gate at the top exit area
                EXIT_WIDTH,
                WALL_THICKNESS  # Same thickness as the wall
            )
            levelgate_spawned = True
            levelgate_used = False
        else:
            levelgate_rect = None  # Remove the levelgate from other rooms



    # Check if player died
    final_stats = calculate_final_stats()
    if final_stats["Health"] <= 0:
        game_over = True

    # Check if player reached exit
    if player_rect.top < (HEIGHT - ROOM_HEIGHT)//2 + WALL_THICKNESS:
        new_room()
        player_rect.centerx = WIDTH//2
        player_rect.bottom = (HEIGHT + ROOM_HEIGHT)//2 - WALL_THICKNESS - 10

    # Draw
    WIN.fill(COLOR_BG)
    for w in walls:
        pygame.draw.rect(WIN, COLOR_WALL, w)
    
    for e in enemies:
        pygame.draw.rect(WIN, COLOR_ENEMY, e["rect"])

        # Draw enemy health bar
        health_bar_width = e["rect"].width
        health_bar_height = 5
        health_ratio = e["health"] / e["max_health"]
        health_bar_bg = pygame.Rect(e["rect"].x, e["rect"].y - health_bar_height - 2, health_bar_width, health_bar_height)
        health_bar_fg = pygame.Rect(e["rect"].x, e["rect"].y - health_bar_height - 2, int(health_bar_width * health_ratio), health_bar_height)
        pygame.draw.rect(WIN, COLOR_HEALTH_BG, health_bar_bg)
        pygame.draw.rect(WIN, COLOR_HEALTH, health_bar_fg)

        # Draw the enemy sword if attacking
        if "sword_rect" in e and current_time < e["swing_end_time"]:
            pygame.draw.rect(WIN, COLOR_SWORD, e["sword_rect"])
    
  
    # Draw the chest if spawned
    if chest_rect:
        pygame.draw.rect(WIN, COLOR_CHEST, chest_rect)
        
        # Draw a smaller square inside to indicate it's opened
        if chest_opened:
            open_rect = chest_rect.inflate(-10, -10)  # Shrink the rect for the "opened" look
            pygame.draw.rect(WIN, COLOR_BG, open_rect)  # Draw smaller square with the floor color

    # Draw the health fountain if it exists
    if health_fountain_rect:
        pygame.draw.rect(WIN, COLOR_FOUNTAIN, health_fountain_rect)
        
        # If used, draw an overlay to indicate the fountain is empty
        if fountain_used:
            used_overlay = health_fountain_rect.inflate(-10, -10)  # Slightly smaller overlay
            pygame.draw.rect(WIN, COLOR_BG, used_overlay)  # Match background color


    # Draw player
    pygame.draw.rect(WIN, COLOR_PLAYER, player_rect)


    # Draw sword hitbox if attacking
    if sword_hitbox:
        pygame.draw.rect(WIN, COLOR_SWORD, sword_hitbox)
    
    # Draw health bar
    bar_width = 200
    bar_height = 20
    final_stats = calculate_final_stats()
    health_ratio = final_stats["Health"] / final_stats["MaxHealth"]
    pygame.draw.rect(WIN, COLOR_HEALTH_BG, (10, 10, bar_width, bar_height))
    pygame.draw.rect(WIN, COLOR_HEALTH, (10, 10, int(bar_width * health_ratio), bar_height))
    
    # Draw stats display
    font_stats = pygame.font.SysFont(None, 24)  # Smaller font for stats
    final_stats = calculate_final_stats()
    draw_stats(WIN, final_stats, font_stats, 10, 40)  # Position under the health bar in the top-left corner
    
    # Display the room number
    font_room = pygame.font.SysFont(None, 36)  # Choose a font and size
    room_text = font_room.render(f"Room #{room_id}", True, (255, 255, 255))  # White text
    WIN.blit(room_text, (WIDTH - 150, 10))  # Position it in the top-right corner
        
    pygame.display.flip()

pygame.quit()
sys.exit()