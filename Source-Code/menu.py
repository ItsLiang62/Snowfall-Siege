import os
import sys
import random
import subprocess
import pygame

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "Assets"))

# Asset helpers
def load_image(name):
    path = os.path.join(ASSETS_DIR, name)
    return pygame.image.load(path)

def play_music():
    bgm_path = os.path.join(ASSETS_DIR, "bgm.mp3")
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.load(bgm_path)
        pygame.mixer.music.play(-1)

# Snow particle
def new_flake(width, height):
    return {
        "x": random.randrange(0, width),
        "y": random.randrange(-height, 0),
        "speed": random.uniform(1.0, 3.5),
        "radius": random.randint(1, 3),
    }

def run_game(script_name):
    # Close menu window and launch the chosen game script, then exit
    pygame.mixer.music.fadeout(300)
    pygame.quit()
    subprocess.run([sys.executable, script_name], cwd=BASE_DIR)
    sys.exit()

def main():
    pygame.init()
    pygame.mixer.init()

    # Load assets
    background_surface = load_image("menu_background.png")

    # Set display before calling convert() to avoid "No video mode has been set"
    screen = pygame.display.set_mode(background_surface.get_size())
    pygame.display.set_caption("Snowfall Siege - Menu")
    background = background_surface.convert()
    clock = pygame.time.Clock()

    play_music()

    font = pygame.font.SysFont("arial", 32, bold=True)
    small_font = pygame.font.SysFont("arial", 24)

    WIDTH, HEIGHT = screen.get_size()

    # Snow setup
    flakes = [new_flake(WIDTH, HEIGHT) for _ in range(120)]

    # Menu states
    state = "main"  # or "stage"

    # Button definitions: (label, action_key)
    main_buttons = [
        ("Start", "start_default"),
        ("Select Stage", "stage_menu"),
        ("Exit", "exit"),
    ]

    stage_buttons = [
        ("Stage 1", "stage1"),
        ("Stage 2", "stage2"),
        ("Back", "back"),
    ]

    def draw_buttons(buttons):
        btn_rects = []
        start_y = HEIGHT // 2 - (len(buttons) * 60) // 2
        for idx, (label, _) in enumerate(buttons):
            rect = pygame.Rect(0, 0, 260, 50)
            rect.center = (WIDTH // 2, start_y + idx * 70)
            btn_rects.append(rect)
            pygame.draw.rect(screen, (0, 0, 0, 128), rect, border_radius=12)
            pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=12)
            text_surf = font.render(label, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)
        return btn_rects

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                buttons = main_buttons if state == "main" else stage_buttons
                rects = draw_buttons(buttons)  # ensure rect list matches current positions
                for rect, (_, action) in zip(rects, buttons):
                    if rect.collidepoint(mouse_pos):
                        if action == "exit":
                            pygame.mixer.music.fadeout(300)
                            pygame.quit()
                            sys.exit()
                        elif action == "stage_menu":
                            state = "stage"
                        elif action == "back":
                            state = "main"
                        elif action == "start_default":
                            run_game("weapon_hunt.py")
                        elif action == "stage1":
                            run_game("weapon_hunt.py")
                        elif action == "stage2":
                            run_game("meltdown.py")

        # Draw background
        screen.blit(background, (0, 0))

        # Snow update/draw
        for flake in flakes:
            flake["y"] += flake["speed"]
            flake["x"] += random.uniform(-0.5, 0.5)
            if flake["y"] > HEIGHT:
                flake.update(new_flake(WIDTH, HEIGHT))
                flake["y"] = -flake["radius"]
            pygame.draw.circle(screen, (255, 255, 255), (int(flake["x"]), int(flake["y"])), flake["radius"])

        # Buttons
        current_buttons = main_buttons if state == "main" else stage_buttons
        draw_buttons(current_buttons)

        # Subtitle text (raised position + blinking)
        subtitle = "Press Start to play" if state == "main" else "Choose a stage"
        ticks = pygame.time.get_ticks()
        blink_on = (ticks // 500) % 2 == 0
        if blink_on:
            subtitle_surf = small_font.render(subtitle, True, (255, 255, 255))
            subtitle_rect = subtitle_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 170))
            screen.blit(subtitle_surf, subtitle_rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.mixer.music.fadeout(500)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
