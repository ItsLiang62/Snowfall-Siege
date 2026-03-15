import pygame
import sys
import random
import math
import os

pygame.init()
pygame.mixer.init()

# =========================
# Paths
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "..", "Assets")

# =========================
# Helper Functions
# =========================
def load_scaled_image(file_name, scale_factor):
    path = os.path.join(ASSET_DIR, file_name)
    original = pygame.image.load(path).convert_alpha()
    width = int(original.get_width() * scale_factor)
    height = int(original.get_height() * scale_factor)
    return pygame.transform.smoothscale(original, (width, height))

def build_wall_mask_from_maze(maze_surface):
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
    dx = target_x - monster_x
    dy = target_y - monster_y
    dist = math.hypot(dx, dy)

    if dist == 0:
        return 0, 0

    move_x = (dx / dist) * speed
    move_y = (dy / dist) * speed
    return move_x, move_y

def get_bullet_velocity(direction, speed):
    if direction == "UP":
        return 0, -speed
    if direction == "DOWN":
        return 0, speed
    if direction == "LEFT":
        return -speed, 0
    return speed, 0

def draw_health_bar(surface, x, y, width, height, current_hp, max_hp, border_color, fill_color, bg_color):
    pygame.draw.rect(surface, bg_color, (x, y, width, height))
    ratio = max(current_hp, 0) / max_hp
    pygame.draw.rect(surface, fill_color, (x, y, int(width * ratio), height))
    pygame.draw.rect(surface, border_color, (x, y, width, height), 2)

def create_monsters():
    return [
        {"x": 350.0, "y": 90.0, "dx": 2.0, "dy": 0.0, "speed": 2.0, "patrol_timer": 0, "hp": 5, "alive": True},
        {"x": 980.0, "y": 35.0, "dx": -2.0, "dy": 0.0, "speed": 2.0, "patrol_timer": 0, "hp": 5, "alive": True},
        {"x": 180.0, "y": 500.0, "dx": 0.0, "dy": -2.0, "speed": 2.0, "patrol_timer": 0, "hp": 5, "alive": True},
        {"x": 1000.0, "y": 520.0, "dx": 0.0, "dy": -2.0, "speed": 2.0, "patrol_timer": 0, "hp": 5, "alive": True}
    ]

def create_ammos():
    return [
        {"x": 205, "y": 160, "collected": False},
        {"x": 820, "y": 80, "collected": False},
        {"x": 0, "y": 550, "collected": False}
    ]

def reset_game(player_stand_img):
    return {
        "player_x": 1000.0,
        "player_y": 700.0,
        "player_direction": "RIGHT",
        "current_player_image": player_stand_img,
        "player_hp": 3,
        "ammo_count": 10,
        "game_won": False,
        "game_lost": False,
        "show_mission": True,
        "mission_start_time": pygame.time.get_ticks(),
        "last_player_hit_time": 0,
        "last_shot_time": 0,
        "bullets": [],
        "monsters": create_monsters(),
        "ammos": create_ammos()
    }

# =========================
# Load Maze
# =========================
maze_raw = pygame.image.load(os.path.join(ASSET_DIR, "maze_level2.png"))
scale_factor = 0.7
maze_width = int(maze_raw.get_width() * scale_factor)
maze_height = int(maze_raw.get_height() * scale_factor)

screen = pygame.display.set_mode((maze_width, maze_height))
pygame.display.set_caption("Snowfall Siege - Level 2 Enhanced")

maze_raw = maze_raw.convert_alpha()
maze = pygame.transform.smoothscale(maze_raw, (maze_width, maze_height))

# =========================
# Load Assets
# =========================
player_run = load_scaled_image("player_run.png", 0.09)
player_stand = load_scaled_image("player_stand.png", 0.05)
monster_img = load_scaled_image("monster_run.png", 0.11)
ammo_img = load_scaled_image("ammo.png", 0.14)

pickup_sound = pygame.mixer.Sound(os.path.join(ASSET_DIR, "pickup.mp3"))
win_sound = pygame.mixer.Sound(os.path.join(ASSET_DIR, "win.mp3"))

pygame.mixer.music.load(os.path.join(ASSET_DIR, "bgm.mp3"))
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.3)

exit_img = pygame.Surface((35, 35), pygame.SRCALPHA)
exit_img.fill((0, 220, 0))

bullet_img = pygame.Surface((10, 10), pygame.SRCALPHA)
pygame.draw.circle(bullet_img, (0, 180, 255), (5, 5), 5)

# =========================
# Fonts / Clock
# =========================
font = pygame.font.SysFont("arial", 24)
big_font = pygame.font.SysFont("arial", 48, bold=True)
mid_font = pygame.font.SysFont("arial", 30, bold=True)
small_font = pygame.font.SysFont("arial", 20)
clock = pygame.time.Clock()

# =========================
# Collision Masks
# =========================
walls_mask = build_wall_mask_from_maze(maze)
exit_mask = pygame.mask.from_surface(exit_img)
bullet_mask = pygame.mask.from_surface(bullet_img)
monster_mask = pygame.mask.from_surface(monster_img)

# =========================
# Game Constants
# =========================
player_speed = 4
player_max_hp = 3
damage_cooldown = 1000
mission_duration = 4000
exit_x, exit_y = 20, 20
bullet_speed = 10
shoot_cooldown = 250
chase_range = 170
patrol_change_time = 90

# =========================
# Initial Game State
# =========================
game = reset_game(player_stand)

running = True

# =========================
# Main Loop
# =========================
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if game["game_lost"] and event.key == pygame.K_r:
                game = reset_game(player_stand)
                continue

            if (not game["game_won"]) and (not game["game_lost"]) and event.key == pygame.K_SPACE:
                current_time = pygame.time.get_ticks()
                if game["ammo_count"] > 0 and current_time - game["last_shot_time"] >= shoot_cooldown:
                    bullet_dx, bullet_dy = get_bullet_velocity(game["player_direction"], bullet_speed)

                    bullet_x = int(game["player_x"] + game["current_player_image"].get_width() // 2)
                    bullet_y = int(game["player_y"] + game["current_player_image"].get_height() // 2)

                    game["bullets"].append({
                        "x": bullet_x,
                        "y": bullet_y,
                        "dx": bullet_dx,
                        "dy": bullet_dy
                    })

                    game["ammo_count"] -= 1
                    game["last_shot_time"] = current_time

    if not game["game_won"] and not game["game_lost"]:
        keys = pygame.key.get_pressed()
        new_x, new_y = game["player_x"], game["player_y"]
        game["current_player_image"] = player_stand

        if keys[pygame.K_UP]:
            game["current_player_image"] = player_run
            game["player_direction"] = "UP"
            new_y -= player_speed
        elif keys[pygame.K_DOWN]:
            game["current_player_image"] = pygame.transform.flip(player_run, True, False)
            game["player_direction"] = "DOWN"
            new_y += player_speed
        elif keys[pygame.K_LEFT]:
            game["current_player_image"] = pygame.transform.flip(player_run, True, False)
            game["player_direction"] = "LEFT"
            new_x -= player_speed
        elif keys[pygame.K_RIGHT]:
            game["current_player_image"] = player_run
            game["player_direction"] = "RIGHT"
            new_x += player_speed

        player_mask = pygame.mask.from_surface(game["current_player_image"])
        ammo_mask = pygame.mask.from_surface(ammo_img)

        if not is_collision((int(new_x), int(new_y)), player_mask, walls_mask):
            game["player_x"], game["player_y"] = new_x, new_y

        for ammo in game["ammos"]:
            if not ammo["collected"]:
                offset = (int(ammo["x"] - game["player_x"]), int(ammo["y"] - game["player_y"]))
                if player_mask.overlap(ammo_mask, offset):
                    ammo["collected"] = True
                    game["ammo_count"] += 7
                    pickup_sound.play()

        all_monsters_dead = all(not monster["alive"] for monster in game["monsters"])
        exit_offset = (int(exit_x - game["player_x"]), int(exit_y - game["player_y"]))

        if all_monsters_dead and player_mask.overlap(exit_mask, exit_offset):
            game["game_won"] = True
            win_sound.play()

        for monster in game["monsters"]:
            if not monster["alive"]:
                continue

            dist_to_player = distance(monster["x"], monster["y"], game["player_x"], game["player_y"])

            if dist_to_player <= chase_range:
                move_x, move_y = move_toward_target(
                    monster["x"], monster["y"],
                    game["player_x"], game["player_y"],
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
            else:
                monster["patrol_timer"] += 1

                if monster["patrol_timer"] >= patrol_change_time:
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

        current_time = pygame.time.get_ticks()

        for monster in game["monsters"]:
            if not monster["alive"]:
                continue

            offset = (int(monster["x"] - game["player_x"]), int(monster["y"] - game["player_y"]))
            if player_mask.overlap(monster_mask, offset):
                if current_time - game["last_player_hit_time"] >= damage_cooldown:
                    game["player_hp"] -= 1
                    game["last_player_hit_time"] = current_time

                    if game["player_hp"] <= 0:
                        game["player_hp"] = 0
                        game["game_lost"] = True

        bullets_to_remove = []

        for bullet in game["bullets"]:
            bullet["x"] += bullet["dx"]
            bullet["y"] += bullet["dy"]

            if bullet["x"] < 0 or bullet["x"] > maze_width or bullet["y"] < 0 or bullet["y"] > maze_height:
                bullets_to_remove.append(bullet)
                continue

            if is_collision((int(bullet["x"]), int(bullet["y"])), bullet_mask, walls_mask):
                bullets_to_remove.append(bullet)
                continue

            for monster in game["monsters"]:
                if not monster["alive"]:
                    continue

                bullet_to_monster_offset = (
                    int(monster["x"] - bullet["x"]),
                    int(monster["y"] - bullet["y"])
                )

                if bullet_mask.overlap(monster_mask, bullet_to_monster_offset):
                    monster["hp"] -= 1
                    bullets_to_remove.append(bullet)

                    if monster["hp"] <= 0:
                        monster["hp"] = 0
                        monster["alive"] = False
                    break

        for bullet in bullets_to_remove:
            if bullet in game["bullets"]:
                game["bullets"].remove(bullet)

    if game["show_mission"]:
        if pygame.time.get_ticks() - game["mission_start_time"] > mission_duration:
            game["show_mission"] = False

    # =========================
    # Draw
    # =========================
    screen.fill((255, 255, 255))
    screen.blit(maze, (0, 0))

    screen.blit(exit_img, (exit_x, exit_y))
    draw_text(screen, "EXIT", font, (0, 140, 0), exit_x, exit_y + 38)

    for ammo in game["ammos"]:
        if not ammo["collected"]:
            screen.blit(ammo_img, (ammo["x"], ammo["y"]))

    for monster in game["monsters"]:
        if monster["alive"]:
            screen.blit(monster_img, (int(monster["x"]), int(monster["y"])))
            draw_health_bar(
                screen,
                int(monster["x"]),
                int(monster["y"]) - 10,
                45,
                6,
                monster["hp"],
                5,
                (0, 0, 0),
                (220, 0, 0),
                (180, 180, 180)
            )

    for bullet in game["bullets"]:
        screen.blit(bullet_img, (int(bullet["x"]), int(bullet["y"])))

    if not game["game_lost"]:
        screen.blit(game["current_player_image"], (int(game["player_x"]), int(game["player_y"])))

    draw_text(screen, f"Ammo: {game['ammo_count']}", font, (0, 0, 0), 20, maze_height - 80)
    draw_text(screen, f"Monsters Left: {sum(1 for monster in game['monsters'] if monster['alive'])}", font, (0, 0, 0), 20, maze_height - 50)
    draw_text(screen, "Player HP", small_font, (0, 0, 0), 20, maze_height - 115)

    draw_health_bar(
        screen,
        20,
        maze_height - 95,
        120,
        18,
        game["player_hp"],
        player_max_hp,
        (0, 0, 0),
        (0, 200, 0),
        (180, 180, 180)
    )

    if game["show_mission"]:
        mission_bg = pygame.Surface((maze_width - 120, 100), pygame.SRCALPHA)
        mission_bg.fill((0, 0, 0, 170))
        screen.blit(mission_bg, (60, 40))
        draw_text(screen, "MISSION:", mid_font, (255, 255, 0), 90, 55)
        draw_text(screen, "Defeat all monsters before leaving the maze!", font, (255, 255, 255), 90, 95)

    if game["game_won"]:
        overlay = pygame.Surface((maze_width, maze_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        draw_text(screen, "VICTORY", big_font, (0, 255, 120), maze_width // 2 - 110, maze_height // 2 - 50)
        draw_text(screen, "All monsters defeated. You escaped!", font, (255, 255, 255), maze_width // 2 - 170, maze_height // 2 + 10)

    if game["game_lost"]:
        overlay = pygame.Surface((maze_width, maze_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        draw_text(screen, "DEFEATED", big_font, (255, 60, 60), maze_width // 2 - 120, maze_height // 2 - 60)
        draw_text(screen, "The monsters caught you.", font, (255, 255, 255), maze_width // 2 - 120, maze_height // 2)
        draw_text(screen, "Press R to Try Again", font, (255, 255, 0), maze_width // 2 - 120, maze_height // 2 + 40)

    pygame.display.flip()

pygame.quit()
sys.exit()