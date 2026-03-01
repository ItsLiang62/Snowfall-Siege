import pygame
import sys
import random

pygame.init()

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
player_run = load_scaled_image("player_run.png", 0.12)
player_stand = load_scaled_image("player_stand.png", 0.06)
monster_run = load_scaled_image("monster_run.png", 0.12)
snowball_gun = load_scaled_image("snowball_gun_2d.png", 0.05)

screen = pygame.display.set_mode((maze.get_width(), maze.get_height()))
pygame.display.set_caption("Weapon Hunt")

maze = maze.convert_alpha()
player_run = player_run.convert_alpha()
player_stand = player_stand.convert_alpha()
monster_run = monster_run.convert_alpha()
snowball_gun = snowball_gun.convert_alpha()

walls_mask = pygame.mask.from_threshold(maze, (0,0,0,255), (1,1,1,255))
walls_mask.invert()

player_x, player_y = 480, 560
monster_x, monster_y = 110, 110
gun_x, gun_y = 815, 220
gun_collected = False
player_speed = 5
monster_speed = 8
monster_direction = new_monster_direction(monster_speed, monster_run)

clock = pygame.time.Clock()

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    player = player_stand
    monster = monster_direction[2]

    keys = pygame.key.get_pressed()
    new_player_x, new_player_y = player_x, player_y
    new_monster_x, new_monster_y = monster_x + monster_direction[0], monster_y + monster_direction[1]

    if (keys[pygame.K_UP]):
        player = player_run
        new_player_y -= player_speed
    elif (keys[pygame.K_DOWN]):
        player = pygame.transform.flip(player_run, True, False)
        new_player_y += player_speed
    elif (keys[pygame.K_LEFT]):
        player = pygame.transform.flip(player_run, True, False)
        new_player_x -= player_speed
    elif (keys[pygame.K_RIGHT]):
        player = player_run
        new_player_x += player_speed

    player_mask = pygame.mask.from_surface(player)
    monster_mask = pygame.mask.from_surface(monster)
    snowball_gun_mask = pygame.mask.from_surface(snowball_gun)

    if not is_collision((new_player_x, new_player_y), player_mask, walls_mask):
        player_x, player_y = new_player_x, new_player_y

    if not is_collision((new_monster_x, new_monster_y), monster_mask, walls_mask):
        monster_x, monster_y = new_monster_x, new_monster_y
    else:
        monster_direction = new_monster_direction(monster_speed, monster_run)

    offset = (gun_x - player_x, gun_y - player_y)
    if player_mask.overlap(snowball_gun_mask, offset):
        gun_collected = True

    screen.fill((255, 255, 255))
    screen.blit(maze, (0, 0))
    screen.blit(player, (player_x, player_y))
    screen.blit(monster, (monster_x, monster_y))
    if not gun_collected:
        screen.blit(snowball_gun, (gun_x, gun_y))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()