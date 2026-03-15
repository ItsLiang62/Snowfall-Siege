import pygame
import sys
import random
import os
import subprocess

pygame.init()
pygame.mixer.init()

def load_scaled_image(file_name, scale_factor):
    original = pygame.image.load("../Assets/" + file_name)
    width = original.get_width() * scale_factor
    height = original.get_height() * scale_factor
    return pygame.transform.smoothscale(original, (width, height))

def is_collision(player_pos, player_mask, walls_mask):
    collision_point = walls_mask.overlap(player_mask, player_pos)
    return collision_point is not None

def new_monster_direction(monster_speed, monster):
    directions = [
        (0, -monster_speed, monster), # Up
        (0, monster_speed, pygame.transform.flip(monster, True, False)), # Down
        (-monster_speed, 0, pygame.transform.flip(monster, True, False)), # Left
        (monster_speed, 0, monster), # Right
        (-monster_speed, -monster_speed, pygame.transform.flip(monster, True, False)), # Up-Left
        (monster_speed, -monster_speed, monster), # Up-Right
        (-monster_speed, monster_speed, pygame.transform.flip(monster, True, False)), # Down-Left
        (monster_speed, monster_speed, monster) # Down-Right
    ]

    random.shuffle(directions)

    return directions[0][0] , directions[0][1], directions[0][2]

# Load maze original as background
# Adjust scale factor of objects to fit maze path
maze = load_scaled_image("maze.png", 0.7)
player_run = load_scaled_image("player_run.png", 0.10)
player_stand = load_scaled_image("player_stand.png", 0.05)
monster_run = load_scaled_image("monster_run.png", 0.12)
snowball_gun = load_scaled_image("snowball_gun_2d.png", 0.05)

screen = pygame.display.set_mode((maze.get_width(), maze.get_height()))
pygame.display.set_caption("Weapon Hunt")

maze = maze.convert_alpha()
player_run = player_run.convert_alpha()
player_stand = player_stand.convert_alpha()
monster_run = monster_run.convert_alpha()
snowball_gun = snowball_gun.convert_alpha()
# Load and scale exit image after display is set
exit_raw = pygame.image.load("../Assets/exit.png").convert_alpha()
exit_img = pygame.transform.smoothscale(
    exit_raw,
    (int(exit_raw.get_width() * 0.2), int(exit_raw.get_height() * 0.2))
)
exit_mask = pygame.mask.from_surface(exit_img)
fail_sound = pygame.mixer.Sound("../Assets/fail_sfx.mp3")
win_sound = pygame.mixer.Sound("../Assets/win.mp3")

walls_mask = pygame.mask.from_threshold(maze, (0,0,0,255), (1,1,1,255))
walls_mask.invert()

# Music
pygame.mixer.music.load("../Assets/bgm.mp3")
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.3)

# State helpers
def reset_game():
    global player_x, player_y, monster_x, monster_y, gun_collected, monster_direction, game_state, fail_played, win_played
    player_x, player_y = 110, 465
    monster_x, monster_y = 110, 110
    gun_collected = False
    monster_direction = new_monster_direction(monster_speed, monster_run)
    game_state = "playing"
    fail_played = False
    win_played = False

def go_to_menu():
    pygame.mixer.music.fadeout(300)
    # Launch menu without waiting, then close this game window
    subprocess.Popen([sys.executable, "menu.py"], cwd=os.path.dirname(__file__))
    pygame.quit()
    sys.exit()

def go_to_next_stage():
    pygame.mixer.music.fadeout(300)
    subprocess.run([sys.executable, "meltdown.py"], cwd=os.path.dirname(__file__))
    pygame.quit()
    sys.exit()

player_x, player_y = 110, 465
monster_x, monster_y = 110, 110
gun_x, gun_y = 815, 220
exit_x, exit_y = 475, 590
gun_collected = False
player_speed = 5
monster_speed = 8
monster_direction = new_monster_direction(monster_speed, monster_run)
game_state = "playing"
fail_played = False
win_played = False

clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 28, bold=True)

WIDTH, HEIGHT = screen.get_width(), screen.get_height()
snow_colors = [
    (240, 248, 255),  # baby blue-ish (AliceBlue)
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

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if game_state == "playing":
                game_state = "pause"
            elif game_state == "pause":
                game_state = "playing"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_state != "playing":
            mx, my = event.pos
            buttons = []
            if game_state == "lose":
                buttons = [("Retry", "retry"), ("Exit to Menu", "menu")]
            elif game_state == "pause":
                buttons = [("Continue", "continue"), ("Retry", "retry"), ("Exit to Menu", "menu")]
            elif game_state == "win":
                buttons = [("Next Stage", "next"), ("Exit to Menu", "menu")]
            start_y = maze.get_height() // 2 - 20
            for i, (label, action) in enumerate(buttons):
                rect = pygame.Rect(0, 0, 220, 50)
                rect.center = (maze.get_width() // 2, start_y + i * 70)
                if rect.collidepoint(mx, my):
                    if action == "retry":
                        reset_game()
                    elif action == "menu":
                        go_to_menu()
                    elif action == "continue":
                        game_state = "playing"
                    elif action == "next":
                        go_to_next_stage()
                    break
    
    player = player_stand
    keys = pygame.key.get_pressed()
    new_player_x, new_player_y = player_x, player_y
    new_monster_x, new_monster_y = monster_x + monster_direction[0], monster_y + monster_direction[1]
    monster = monster_direction[2]

    # If paused but movement key is pressed, resume play
    if game_state == "pause" and (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_DOWN] or keys[pygame.K_s] or keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
        game_state = "playing"

    # Movement intent with smoother wall slide (no rapid facing flips at corners)
    dx, dy = 0, 0
    if game_state == "playing" and (keys[pygame.K_UP] or keys[pygame.K_w]):
        player = player_run
        dy = -player_speed
    elif game_state == "playing" and (keys[pygame.K_DOWN] or keys[pygame.K_s]):
        player = pygame.transform.flip(player_run, True, False)
        dy = player_speed
    elif game_state == "playing" and (keys[pygame.K_LEFT] or keys[pygame.K_a]):
        player = pygame.transform.flip(player_run, True, False)
        dx = -player_speed
    elif game_state == "playing" and (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
        player = player_run
        dx = player_speed

    attempts = []
    if dx == 0 and dy == 0:
        attempts = [(0, 0)]
    else:
        # Try intended move first; if blocked, try perpendicular slides (keep same facing sprite)
        attempts.append((dx, dy))
        if dy != 0:
            attempts.append((-player_speed, 0))
            attempts.append((player_speed, 0))
        if dx != 0:
            attempts.append((0, -player_speed))
            attempts.append((0, player_speed))

    for attempt_dx, attempt_dy in attempts:
        candidate_x = player_x + attempt_dx
        candidate_y = player_y + attempt_dy
        player_mask = pygame.mask.from_surface(player)
        if not is_collision((candidate_x, candidate_y), player_mask, walls_mask):
            new_player_x, new_player_y = candidate_x, candidate_y
            break

    player_mask = pygame.mask.from_surface(player)
    monster_mask = pygame.mask.from_surface(monster)
    snowball_gun_mask = pygame.mask.from_surface(snowball_gun)

    if game_state == "playing" and not is_collision((new_player_x, new_player_y), player_mask, walls_mask):
        player_x, player_y = new_player_x, new_player_y

    if game_state == "playing":
        if not is_collision((new_monster_x, new_monster_y), monster_mask, walls_mask):
            monster_x, monster_y = new_monster_x, new_monster_y
        else:
            monster_direction = new_monster_direction(monster_speed, monster_run)

    if game_state == "playing":
        offset = (gun_x - player_x, gun_y - player_y)
        if player_mask.overlap(snowball_gun_mask, offset):
            gun_collected = True

        exit_offset = (exit_x - player_x, exit_y - player_y)
        if gun_collected and player_mask.overlap(exit_mask, exit_offset):
            game_state = "win"
            if not win_played:
                win_sound.play()
                win_played = True

        monster_offset = (int(monster_x - player_x), int(monster_y - player_y))
        if player_mask.overlap(monster_mask, monster_offset):
            game_state = "lose"
            if not fail_played:
                fail_sound.play()
                fail_played = True

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

    screen.blit(player, (player_x, player_y))
    screen.blit(monster, (monster_x, monster_y))
    if not gun_collected:
        screen.blit(snowball_gun, (gun_x, gun_y))
    screen.blit(exit_img, (exit_x, exit_y))

    if game_state != "playing":
        overlay = pygame.Surface((maze.get_width(), maze.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        title = "You Win!" if game_state == "win" else ("You Lose!" if game_state == "lose" else "Paused")
        title_surf = font.render(title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(maze.get_width() // 2, maze.get_height() // 2 - 100))
        screen.blit(title_surf, title_rect)

        buttons = []
        if game_state == "lose":
            buttons = [("Retry", "retry"), ("Exit to Menu", "menu")]
        elif game_state == "pause":
            buttons = [("Continue", "continue"), ("Retry", "retry"), ("Exit to Menu", "menu")]
        elif game_state == "win":
            buttons = [("Next Stage", "next"), ("Exit to Menu", "menu")]

        start_y = maze.get_height() // 2 - 20
        for i, (label, _) in enumerate(buttons):
            rect = pygame.Rect(0, 0, 220, 50)
            rect.center = (maze.get_width() // 2, start_y + i * 70)
            pygame.draw.rect(screen, (0, 0, 0, 180), rect, border_radius=12)
            pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=12)
            text = font.render(label, True, (255, 255, 255))
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
