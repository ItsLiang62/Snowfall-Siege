import pygame
import sys
import random
import math
import os
import subprocess

pygame.init()
pygame.mixer.init()
# =========================
# Helper Functions
# =========================
def load_scaled_image(file_name, scale_factor):
    original = pygame.image.load("../Assets/" + file_name).convert_alpha()
    width = int(original.get_width() * scale_factor)
    height = int(original.get_height() * scale_factor)
    return pygame.transform.smoothscale(original, (width, height))

def build_wall_mask_from_maze(maze_surface):
    """
    Detect the light gray floor as walkable area,
    then invert it so walls become solid.
    """
    walkable_mask = pygame.mask.from_threshold(
        maze_surface,
        (230, 230, 230, 255),
        (35, 35, 35, 255)
    )
    walkable_mask.invert()
    return walkable_mask

def is_collision(obj_pos, obj_mask, walls_mask):
    return walls_mask.overlap(obj_mask, obj_pos) is not None

def draw_text(surface, text, font, color, x, y):
    img = font.render(text, True, color)
    surface.blit(img, (x, y))

def new_monster_direction(speed):
    directions = [
        (speed, 0),
        (-speed, 0),
        (0, speed),
        (0, -speed),
    ]
    return random.choice(directions)

def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def move_toward_target(monster_x, monster_y, target_x, target_y, speed):
    """
    Return dx, dy that moves the monster toward the target.
    """
    dx = target_x - monster_x
    dy = target_y - monster_y
    dist = math.hypot(dx, dy)

    if dist == 0:
        return 0, 0

    move_x = (dx / dist) * speed
    move_y = (dy / dist) * speed

    return move_x, move_y


# =========================
# Load Maze
# =========================
maze_raw = pygame.image.load("../Assets/maze_level2.png")

scale_factor = 0.60  # smaller window
maze_width = int(maze_raw.get_width() * scale_factor)
maze_height = int(maze_raw.get_height() * scale_factor)

screen = pygame.display.set_mode((maze_width, maze_height))
pygame.display.set_caption("Snowfall Siege - Level 2")

maze_raw = maze_raw.convert_alpha()
maze = pygame.transform.smoothscale(maze_raw, (maze_width, maze_height))

# =========================
# Load Assets
# =========================
player_run = load_scaled_image("player_run.png", 0.09)
player_stand = load_scaled_image("player_stand.png", 0.05)
monster_img = load_scaled_image("monster_run.png", 0.11)
ammo_img = load_scaled_image("ammo.png", 0.14)

pickup_sound = pygame.mixer.Sound("../Assets/pickup.mp3")
win_sound = pygame.mixer.Sound("../Assets/win.mp3")

pygame.mixer.music.load("../Assets/bgm.mp3")
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.3)
# Exit block (temporary)
exit_img = pygame.Surface((35, 35), pygame.SRCALPHA)
exit_img.fill((0, 220, 0))

# Snow overlay setup
WIDTH, HEIGHT = screen.get_width(), screen.get_height()
snow_colors = [
    (240, 248, 255),  # baby blue-ish
    (0, 0, 0),        # black
    (255, 255, 255),  # white
]
flakes = [
    {
        "x": random.randrange(0, WIDTH),
        "y": random.randrange(-HEIGHT, 0),
        "speed": random.uniform(1.0, 3.5),
        "radius": random.randint(1, 3),
        "color": random.choice(snow_colors),
    }
    for _ in range(120)
]

# =========================
# Fonts / Clock
# =========================
font = pygame.font.SysFont("arial", 24)
big_font = pygame.font.SysFont("arial", 46, bold=True)
clock = pygame.time.Clock()

# =========================
# Collision Mask
# =========================
walls_mask = build_wall_mask_from_maze(maze)

# =========================
# Game Variables
# =========================
player_speed = 4
ammo_count = 0
game_won = False
running = True
game_paused = False

player_x, player_y = 1000, 700

exit_x, exit_y = 20 , -30

monsters = [
    {"x": 350.0, "y": 90.0, "dx": 2.0, "dy": 0.0, "speed": 2.0, "patrol_timer": 0},
    {"x": 980.0, "y": 35.0, "dx": -2.0, "dy": 0.0, "speed": 2.0, "patrol_timer": 0},
    {"x": 180.0, "y": 500.0, "dx": 0.0, "dy": -2.0, "speed": 2.0, "patrol_timer": 0},
    {"x": 1000.0, "y": 520.0, "dx": 0.0, "dy": -2.0, "speed": 2.0, "patrol_timer": 0}
]

ammos = [
    {"x": 205, "y": 160, "collected": False},
    {"x": 820, "y": 80, "collected": False},
    {"x": 0, "y": 550, "collected": False}
]

# AI settings
CHASE_RANGE = 170
PATROL_CHANGE_TIME = 90

def go_to_menu():
    pygame.mixer.music.fadeout(300)
    subprocess.Popen([sys.executable, "menu.py"], cwd=os.path.dirname(__file__))
    pygame.quit()
    sys.exit()

# =========================
# Main Loop
# =========================
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            go_to_menu()

    current_player_image = player_stand

    # =========================
    # Player Movement
    # =========================
    if not game_won:
        keys = pygame.key.get_pressed()
        new_x, new_y = player_x, player_y

        if keys[pygame.K_UP]:
            current_player_image = player_run
            new_y -= player_speed
        elif keys[pygame.K_DOWN]:
            current_player_image = pygame.transform.flip(player_run, True, False)
            new_y += player_speed
        elif keys[pygame.K_LEFT]:
            current_player_image = pygame.transform.flip(player_run, True, False)
            new_x -= player_speed
        elif keys[pygame.K_RIGHT]:
            current_player_image = player_run
            new_x += player_speed

        player_mask = pygame.mask.from_surface(current_player_image)
        ammo_mask = pygame.mask.from_surface(ammo_img)
        exit_mask = pygame.mask.from_surface(exit_img)

        if not is_collision((int(new_x), int(new_y)), player_mask, walls_mask):
            player_x, player_y = new_x, new_y

        for ammo in ammos:
            if not ammo["collected"]:
                offset = (int(ammo["x"] - player_x), int(ammo["y"] - player_y))
                if player_mask.overlap(ammo_mask, offset):
                    ammo["collected"] = True
                    ammo_count += 5
                    pickup_sound.play()

        exit_offset = (int(exit_x - player_x), int(exit_y - player_y))
        if player_mask.overlap(exit_mask, exit_offset):
            game_won = True
            win_sound.play()

        # =========================
        # Monster AI
        # =========================
        monster_mask = pygame.mask.from_surface(monster_img)

        for monster in monsters:
            dist_to_player = distance(monster["x"], monster["y"], player_x, player_y)

            # -------- Chase Mode --------
            if dist_to_player <= CHASE_RANGE:
                move_x, move_y = move_toward_target(
                    monster["x"], monster["y"],
                    player_x, player_y,
                    monster["speed"] + 0.6
                )

                test_x = monster["x"] + move_x
                test_y = monster["y"] + move_y

                if not is_collision((int(test_x), int(test_y)), monster_mask, walls_mask):
                    monster["x"] = test_x
                    monster["y"] = test_y
                else:
                    test_x_only = monster["x"] + move_x
                    if not is_collision((int(test_x_only), int(monster["y"])), monster_mask, walls_mask):
                        monster["x"] = test_x_only

                    test_y_only = monster["y"] + move_y
                    if not is_collision((int(monster["x"]), int(test_y_only)), monster_mask, walls_mask):
                        monster["y"] = test_y_only

            # -------- Patrol Mode --------
            else:
                monster["patrol_timer"] += 1

                if monster["patrol_timer"] >= PATROL_CHANGE_TIME:
                    monster["dx"], monster["dy"] = new_monster_direction(monster["speed"])
                    monster["patrol_timer"] = 0

                test_x = monster["x"] + monster["dx"]
                test_y = monster["y"] + monster["dy"]

                if not is_collision((int(test_x), int(test_y)), monster_mask, walls_mask):
                    monster["x"] = test_x
                    monster["y"] = test_y
                else:
                    monster["dx"], monster["dy"] = new_monster_direction(monster["speed"])
                    monster["patrol_timer"] = 0

    # =========================
    # Draw
    # =========================
    screen.fill((255, 255, 255))
    screen.blit(maze, (0, 0))

    # Snow overlay
    for flake in flakes:
        flake["y"] += flake["speed"]
        flake["x"] += random.uniform(-0.5, 0.5)
        if flake["y"] > HEIGHT:
            flake["y"] = -flake["radius"]
            flake["x"] = random.randrange(0, WIDTH)
            flake["color"] = random.choice(snow_colors)
        pygame.draw.circle(screen, flake["color"], (int(flake["x"]), int(flake["y"])), flake["radius"])

    # Exit
    screen.blit(exit_img, (exit_x, exit_y))
    draw_text(screen, "EXIT", font, (0, 140, 0), exit_x, exit_y + 38)

    # Monsters
    for monster in monsters:
        screen.blit(monster_img, (int(monster["x"]), int(monster["y"])))

    # Ammo
    for ammo in ammos:
        if not ammo["collected"]:
            screen.blit(ammo_img, (ammo["x"], ammo["y"]))

    # Player
    if not game_won:
        screen.blit(current_player_image, (int(player_x), int(player_y)))

    # UI
    draw_text(screen, f"Ammo: {ammo_count}", font, (0, 0, 0), 20, maze_height - 35)

    # Win message
    if game_won:
        draw_text(
            screen,
            "YOU ESCAPED!",
            big_font,
            (0, 100, 255),
            maze_width // 2 - 170,
            maze_height // 2 - 20
        )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
