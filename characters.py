import pygame
import os

# Palette for retro procedural sprite
_ = None                       # Transparent
H = (165, 80, 40)              # Brown hair
B = (240, 60, 110)             # Hair bows / ribbons
S = (255, 215, 180)            # Skin tone
E = (30, 30, 40)               # Eyes
D = (59, 130, 246)             # Dress (Blue)
W = (240, 240, 240)            # Socks
K = (180, 40, 60)              # Shoes

PIPPA_PIXELS = [
    [_, _, B, H, H, H, H, H, H, H, H, B, _, _, _, _],
    [_, B, H, H, H, H, H, H, H, H, H, H, B, _, _, _],
    [H, H, H, H, S, S, S, S, S, S, H, H, H, H, _, _],
    [H, H, H, S, S, S, S, S, S, S, S, H, H, H, _, _],
    [H, H, S, S, E, S, S, S, E, S, S, S, H, H, _, _],
    [_, H, S, S, E, S, S, S, E, S, S, S, H, _, _, _],
    [_, _, S, S, S, S, S, S, S, S, S, S, _, _, _, _],
    [_, _, _, S, S, S, B, B, S, S, S, _, _, _, _, _],
    [_, _, D, D, D, D, D, D, D, D, D, D, _, _, _, _],
    [_, D, D, D, D, D, D, D, D, D, D, D, D, _, _, _],
    [_, D, D, D, D, D, D, D, D, D, D, D, D, _, _, _],
    [_, D, D, D, D, D, D, D, D, D, D, D, D, _, _, _],
    [_, _, D, D, D, D, D, D, D, D, D, D, _, _, _, _],
    [_, _, _, S, S, _, _, _, _, S, S, _, _, _, _, _],
    [_, _, _, W, W, _, _, _, _, W, W, _, _, _, _, _],
    [_, _, K, K, K, _, _, _, _, K, K, K, _, _, _, _],
]

def generate_procedural_sprite(pixel_map):
    surface = pygame.Surface((16, 16), pygame.SRCALPHA)
    for y, row in enumerate(pixel_map):
        for x, color in enumerate(row):
            if color is not None:
                surface.set_at((x, y), color)
    return surface

def load_character_sprite(char_name="pippa", target_height=44):
    """
    Loads a sprite and scales it so its height matches target_height exactly,
    preserving the original aspect ratio so characters don't look squished.
    """
    asset_path = os.path.join("assets", f"{char_name}.png")
    
    if os.path.exists(asset_path):
        image = pygame.image.load(asset_path).convert_alpha()
    else:
        image = generate_procedural_sprite(PIPPA_PIXELS)
    
    orig_w, orig_h = image.get_size()
    aspect_ratio = orig_w / orig_h
    target_width = int(target_height * aspect_ratio)
    
    return pygame.transform.scale(image, (target_width, target_height))