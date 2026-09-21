import pygame
import os

# Registry mapping character keys to display info and filenames in assets/
CHARACTERS = {
    "pippa": {
        "name": "Pippa",
        "title": "Curious Adventurer",
        "desc_en": "Quick thinker and math whiz ready for any maze puzzle!",
        "desc_fr": "Esprit vif et as des maths, prête pour chaque énigme !",
    },
    "marryo": {
        "name": "Marryo",
        "title": "Brave Builder",
        "desc_en": "Strong and steady block pusher who loves big numbers.",
        "desc_fr": "Robuste et déterminé, adore pousser les blocs de chiffres.",
    },
    "capivara": {
        "name": "Capivara",
        "title": "Calm Navigator",
        "desc_en": "Gentle friend who never stresses over tricky calculations.",
        "desc_fr": "Ami paisible qui reste toujours zen devant les calculs.",
    },
    "danny": {
        "name": "Danny",
        "title": "Energetic Explorer",
        "desc_en": "Dashes through schools and collects every last gem!",
        "desc_fr": "Fonce à travers les écoles pour attraper toutes les gemmes !",
    },
}

CHARACTER_KEYS = list(CHARACTERS.keys())

# Procedural fallback sprite in case an asset file is missing
_ = None
H = (165, 80, 40)
B = (240, 60, 110)
S = (255, 215, 180)
E = (30, 30, 40)
D = (59, 130, 246)
W = (240, 240, 240)
K = (180, 40, 60)

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
    """ Loads a sprite anchored to the script's directory and scales it preserving aspect ratio. """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    asset_path = os.path.join(base_dir, "assets", f"{char_name}.png")

    image = None
    if os.path.exists(asset_path):
        try:
            image = pygame.image.load(asset_path)
            # Only convert_alpha if the display surface is active and ready
            if pygame.display.get_surface() is not None:
                image = image.convert_alpha()
        except Exception as e:
            print(f"Warning: Failed to load {asset_path}: {e}")
            image = None

    if image is None:
        print(f"Notice: Missing asset at '{asset_path}', using procedural fallback.")
        image = generate_procedural_sprite(PIPPA_PIXELS)

    orig_w, orig_h = image.get_size()
    aspect_ratio = orig_w / max(1, orig_h)
    target_width = max(1, int(target_height * aspect_ratio))

    return pygame.transform.scale(image, (target_width, target_height))