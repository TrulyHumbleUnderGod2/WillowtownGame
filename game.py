# Example file showing a circle moving on screen
import pygame

# pygame setup
pygame.init()

screen = pygame.display.set_mode((640,320))

clock = pygame.time.Clock()
running = True
dt = -0

player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.update()
    clock.tick(60)
