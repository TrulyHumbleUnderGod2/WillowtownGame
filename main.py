import os
import random
import math
from turtle import Screen
import pygame
from os import listdir
from os.path import isfile, join
pygame.init()

pygame.display.set_caption("Willowtown Alpha 0.0.2")

BG_COLOR = (255, 255, 255)
WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites
    
    return all_sprites

def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "PinkMan", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count ==1:
            self.fall_count = 0
            
    def make_hit(self):
        self.hit = True
        self.hit_count = 0
        
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        if self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)


    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name
    
    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height )
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window,offset_x)

    player.draw(window, offset_x)

    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object

def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_a] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()

def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("sky.png")

    block_size = 96

    player = Player(100, 100, 50, 50)
    fire = Fire(400, 510 - block_size - 64, 16, 32)
    fire.on()
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * -1) // block_size)]
    objects = [*floor, Block(0, HEIGHT - block_size * 0, block_size), 
    Block(block_size * 1, HEIGHT - block_size * 6, block_size),  
    Block(block_size * 2, HEIGHT - block_size * 6, block_size), 
    Block(block_size * 4, HEIGHT - block_size * 3.5, block_size), 
    Block(block_size * 5, HEIGHT - block_size * 3.5, block_size),
    Block(block_size * 8, HEIGHT - block_size * 5, block_size),
    Block(block_size * 9, HEIGHT - block_size * 5, block_size),
    Block(block_size * 11, HEIGHT - block_size * 7, block_size),
    Block(block_size * 12, HEIGHT - block_size * 7, block_size),
    Block(block_size * 14, HEIGHT - block_size * 2, block_size),
    Block(block_size * 15, HEIGHT - block_size * 2, block_size),
    Block(block_size * 18, HEIGHT - block_size * 3, block_size),
    Block(block_size * 19, HEIGHT - block_size * 3, block_size),
    Block(block_size * 22, HEIGHT - block_size * 5, block_size),
    Block(block_size * 23, HEIGHT - block_size * 5, block_size),
    Block(block_size * 27, HEIGHT - block_size * 3, block_size),
    Block(block_size * 28, HEIGHT - block_size * 3, block_size),
    Block(block_size * 32, HEIGHT - block_size * 4, block_size),
    Block(block_size * 33, HEIGHT - block_size * 4, block_size),
    Block(block_size * 36, HEIGHT - block_size * 6, block_size),
    Block(block_size * 37, HEIGHT - block_size * 6, block_size),
    Block(block_size * 40, HEIGHT - block_size * 3, block_size),
    Block(block_size * 43, HEIGHT - block_size * 5, block_size),
    Block(block_size * 46, HEIGHT - block_size * 7, block_size),
    Block(block_size * 50, HEIGHT - block_size * 4, block_size),
    Block(block_size * 53, HEIGHT - block_size * 6, block_size),
    Block(block_size * 56, HEIGHT - block_size * 2, block_size),
    Block(block_size * 59, HEIGHT - block_size * 4, block_size),
    Block(block_size * 62, HEIGHT - block_size * 1, block_size),
    Block(block_size * 65, HEIGHT - block_size * 3, block_size),
    Block(block_size * 68, HEIGHT - block_size * 4, block_size),
    Block(block_size * 71, HEIGHT - block_size * 6, block_size),
    Block(block_size * 74, HEIGHT - block_size * 8, block_size),
    Block(block_size * 77, HEIGHT - block_size * 3, block_size),
    Block(block_size * 80, HEIGHT - block_size * 5, block_size),
    Block(block_size * 83, HEIGHT - block_size * 2, block_size),
    Block(block_size * 86, HEIGHT - block_size * 4, block_size),
    Block(block_size * 89, HEIGHT - block_size * 1, block_size),
    Block(block_size * 92, HEIGHT - block_size * 3, block_size),
    Block(block_size * 95, HEIGHT - block_size * 5, block_size),
    Block(block_size * 98, HEIGHT - block_size * 1, block_size),
    Block(block_size * 101, HEIGHT - block_size * 3, block_size),
    Block(block_size * 104, HEIGHT - block_size * 2, block_size),
    Block(block_size * 107, HEIGHT - block_size * 4, block_size),
    Block(block_size * 110, HEIGHT - block_size * 6, block_size),
    Block(block_size * 113, HEIGHT - block_size * 3, block_size),
    Block(block_size * 116, HEIGHT - block_size * 2, block_size),
    Block(block_size * 119, HEIGHT - block_size * 4, block_size),
    Block(block_size * 122, HEIGHT - block_size * 1, block_size),
    Block(block_size * 125, HEIGHT - block_size * 2, block_size),
    Block(block_size * 128, HEIGHT - block_size * 4, block_size),
    Block(block_size * 131, HEIGHT - block_size * 6, block_size),
    Block(block_size * 134, HEIGHT - block_size * 3, block_size),
    Block(block_size * 137, HEIGHT - block_size * 2, block_size),
    Block(block_size * 140, HEIGHT - block_size * 4, block_size),
    Block(block_size * 143, HEIGHT - block_size * 4, block_size),
    Block(block_size * 146, HEIGHT - block_size * 2, block_size),
    Block(block_size * 149, HEIGHT - block_size * 3, block_size),
    Block(block_size * 152, HEIGHT - block_size * 5, block_size),
    Block(block_size * 155, HEIGHT - block_size * 2, block_size),
    Block(block_size * 158, HEIGHT - block_size * 4, block_size),
    Block(block_size * 161, HEIGHT - block_size * 3, block_size),
    Block(block_size * 164, HEIGHT - block_size * 2, block_size),
    Block(block_size * 167, HEIGHT - block_size * 4, block_size),
    Block(block_size * 170, HEIGHT - block_size * 1, block_size),
    Block(block_size * 173, HEIGHT - block_size * 3, block_size),
    Block(block_size * 176, HEIGHT - block_size * 2, block_size),
    Block(block_size * 179, HEIGHT - block_size * 4, block_size),
    Block(block_size * 182, HEIGHT - block_size * 6, block_size),
    Block(block_size * 185, HEIGHT - block_size * 8, block_size),
    Block(block_size * 187, HEIGHT - block_size * 1, block_size),
    Block(block_size * 188, HEIGHT - block_size * 1, block_size),
    Block(block_size * 189, HEIGHT - block_size * 1, block_size),
    Block(block_size * 190, HEIGHT - block_size * 1, block_size),
    Block(block_size * 191, HEIGHT - block_size * 1, block_size),
    Block(block_size * 192, HEIGHT - block_size * 1, block_size),
    Block(block_size * 193, HEIGHT - block_size * 1, block_size),
    Block(block_size * 194, HEIGHT - block_size * 1, block_size),
    Block(block_size * 195, HEIGHT - block_size * 1, block_size),
    Block(block_size * 196, HEIGHT - block_size * 1, block_size),
    Block(block_size * 197, HEIGHT - block_size * 1, block_size),
    Block(block_size * 198, HEIGHT - block_size * 1, block_size),
    Block(block_size * 199, HEIGHT - block_size * 1, block_size),
    Block(block_size * 200, HEIGHT - block_size * 1, block_size),
    Block(block_size * 201, HEIGHT - block_size * 1, block_size),
    Block(block_size * 202, HEIGHT - block_size * 1, block_size),
    Block(block_size * 203, HEIGHT - block_size * 1, block_size),
    Block(block_size * 204, HEIGHT - block_size * 1, block_size),
    Block(block_size * 205, HEIGHT - block_size * 1, block_size),
    fire]
    
    offset_x = 0
    scroll_area_width = 200

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        fire.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or ((player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel 
# Load the sprites
boss_sprite = pygame.image.load(join("assests", "boss_sprite.png")).convert_alpha()
fireball_sprite = pygame.image.load(join("assests", "fireball_sprite.png")).convert_alpha()

# Constants for Boss
BOSS_WIDTH = 92
BOSS_HEIGHT = 92
BOSS_SHOOT_INTERVAL = 2000  # Milliseconds

# Constants for Fireball
FIREBALL_WIDTH = 92
FIREBALL_HEIGHT = 92
FIREBALL_SPEED = 5


class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.images = [
            boss_sprite.subsurface((0, 0, BOSS_WIDTH, BOSS_HEIGHT)),
            boss_sprite.subsurface((0, BOSS_HEIGHT, BOSS_WIDTH, BOSS_HEIGHT)),
            boss_sprite.subsurface((0, BOSS_HEIGHT * 2, BOSS_WIDTH, BOSS_HEIGHT)),
        ]
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.shoot_timer = pygame.time.get_ticks()
        self.animation_timer = pygame.time.get_ticks()

    def update(self):
        current_time = pygame.time.get_ticks()

        # Animate boss
        if current_time - self.animation_timer > 300:  # Change frame every 300ms
            self.image = self.images[(self.images.index(self.image) + 1) % len(self.images)]
            self.animation_timer = current_time

        # Check if boss should shoot
        if current_time - self.shoot_timer > BOSS_SHOOT_INTERVAL:
            self.shoot_timer = current_time
            return True  # Signal to shoot fireball
        return False


class Fireball(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = fireball_sprite
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def update(self):
        self.rect.x -= FIREBALL_SPEED
        if self.rect.right < 0:
            self.kill()


# Initialize sprite groups
all_sprites = pygame.sprite.Group()
fireballs = pygame.sprite.Group()

# Create the boss
boss = Boss(SCREEN_WIDTH - BOSS_WIDTH, SCREEN_HEIGHT // 2)
all_sprites.add(boss)

# Main game loop
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update boss and check if it shoots
    if boss.update():
        fireball = Fireball(boss.rect.left - FIREBALL_WIDTH, boss.rect.centery - FIREBALL_HEIGHT // 2)
        fireballs.add(fireball)
        all_sprites.add(fireball)

    # Update all sprites
    all_sprites.update()

    # Clear screen
    screen.fill(BG_COLOR)

    # Draw all sprites
    all_sprites.draw(screen)

    # Update display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)
    
    pygame.quit
    quit()


if __name__ == "__main__":
    main(window)

