import pygame
import sys
import random
import array
import math
import os
import hashlib
import threading
import shutil
import subprocess
from characters import load_character_sprite
from gameplay_parameters import LEVELS, load_mazes

pygame.init()
pygame.font.init()

# Controller hardware initialization
pygame.event.pump()
pygame.joystick.init()
pygame.event.pump()

WIDTH, HEIGHT = 900, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pippa & Mario: Math Quest")
clock = pygame.time.Clock()

# Color Palette
BG_COLOR = (24, 26, 36)
COLOR_WALL = (45, 52, 70)
COLOR_TEXT_DIM = (100, 110, 135)
COLOR_TEXT_LIT = (255, 255, 255)
COLOR_ACCENT = (255, 204, 0)
COLOR_TARGET = (129, 140, 248)
COLOR_FEEDBACK = (239, 68, 68)
COLOR_SUCCESS = (34, 197, 94)

COLOR_FR_SCHOOL = (37, 99, 235)    # French Blue
COLOR_EN_SCHOOL = (225, 29, 72)    # English Crimson
COLOR_SCHOOL_DONE = (75, 85, 105)  # Dimmed graduated building

COLOR_RUBY = (239, 68, 68)
COLOR_EMERALD = (16, 185, 129)
COLOR_DIAMOND = (56, 189, 248)

FONT_BIG = pygame.font.Font(None, 84)
FONT_MED = pygame.font.Font(None, 38)
FONT_SMALL = pygame.font.Font(None, 24)

# Fallback maze in case mazes.txt is missing
DEFAULT_MAZE = [
    "##################",
    "# . . . . P . .  #",
    "#. ### . . ### . #",
    "#. # . . . . # . #",
    "#. # . ### . # . #",
    "#. . . . . . . . #",
    "### . ##### . ####",
    "# . . # . . . .  #",
    "F . . . . # . .  E",
    "##################"
]

# -------------------------------------------------------------
# RETRO SOUND SYNTHESIZER
# -------------------------------------------------------------
class SoundFX:
    def __init__(self):
        self.enabled = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(8)
            self.sfx_channel = pygame.mixer.Channel(0)
            self.sample_rate = 22050
            self.gem_sound = self._make_gem_sound()
            self.success_sound = self._make_success_sound()
            self.buzz_sound = self._make_buzz_sound()
            self.level_sound = self._make_level_up_sound()
            self.enabled = True
        except Exception as e:
            print(f"Audio notice: {e}")

    def _tone(self, freq, duration_s, volume=0.25):
        num_samples = int(self.sample_rate * duration_s)
        buf = array.array('h')
        for i in range(num_samples):
            t = i / self.sample_rate
            decay = max(0.0, 1.0 - (i / num_samples))
            val = int(32767 * volume * decay * math.sin(2 * math.pi * freq * t))
            buf.append(val)
        return buf

    def _make_gem_sound(self):
        b1 = self._tone(987, 0.05, 0.20)
        b2 = self._tone(1318, 0.12, 0.25)
        b1.extend(b2)
        return pygame.mixer.Sound(buffer=b1.tobytes())

    def _make_success_sound(self):
        notes = [523, 659, 784, 1046]
        comb = array.array('h')
        for idx, freq in enumerate(notes):
            dur = 0.07 if idx < 3 else 0.25
            comb.extend(self._tone(freq, dur, 0.25))
        return pygame.mixer.Sound(buffer=comb.tobytes())

    def _make_buzz_sound(self):
        return pygame.mixer.Sound(buffer=self._tone(140, 0.18, 0.25).tobytes())

    def _make_level_up_sound(self):
        fanfare = [523, 784, 1046, 1318, 1568]
        comb = array.array('h')
        for idx, freq in enumerate(notes := fanfare):
            dur = 0.08 if idx < 4 else 0.45
            comb.extend(self._tone(freq, dur, 0.30))
        return pygame.mixer.Sound(buffer=comb.tobytes())

    def play_gem(self):
        if self.enabled: self.sfx_channel.play(self.gem_sound)

    def play_success(self):
        if self.enabled: self.sfx_channel.play(self.success_sound)

    def play_buzz(self):
        if self.enabled: self.sfx_channel.play(self.buzz_sound)

    def play_level_up(self):
        if self.enabled: self.sfx_channel.play(self.level_sound)

# -------------------------------------------------------------
# HIGH QUALITY CACHED SPEECH ENGINE
# -------------------------------------------------------------
class SmartSpeechEngine:
    def __init__(self):
        self.cache_dir = "voice_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.voice_channel = pygame.mixer.Channel(1)
        self.has_gtts = False
        self.is_downloading = False
        self.fallback_proc = None
        
        try:
            import gtts
            self.has_gtts = True
        except ImportError:
            pass

    def is_busy(self):
        proc_busy = (self.fallback_proc is not None and self.fallback_proc.poll() is None)
        return self.is_downloading or self.voice_channel.get_busy() or proc_busy

    def stop(self):
        self.is_downloading = False
        if self.voice_channel.get_busy():
            self.voice_channel.stop()
        if self.fallback_proc and self.fallback_proc.poll() is None:
            try:
                self.fallback_proc.terminate()
            except Exception:
                pass
            self.fallback_proc = None

    def speak(self, text, lang="en"):
        if not text:
            return
        self.stop()

        slug = hashlib.md5(f"{lang}_{text}".encode('utf-8')).hexdigest()
        filepath = os.path.join(self.cache_dir, f"{lang}_{slug}.mp3")

        if os.path.exists(filepath):
            try:
                sound = pygame.mixer.Sound(filepath)
                self.voice_channel.play(sound)
                return
            except Exception:
                pass

        if self.has_gtts:
            self.is_downloading = True
            def _download_and_play(target_path=filepath):
                try:
                    from gtts import gTTS
                    tts = gTTS(text=text, lang=lang, slow=False)
                    tts.save(target_path)
                    if self.is_downloading:
                        sound = pygame.mixer.Sound(target_path)
                        self.voice_channel.play(sound)
                except Exception:
                    self._system_fallback(text, lang)
                finally:
                    self.is_downloading = False

            threading.Thread(target=_download_and_play, daemon=True).start()
        else:
            self._system_fallback(text, lang)

    def _system_fallback(self, text, lang):
        try:
            if shutil.which("say"):
                self.fallback_proc = subprocess.Popen(["say", "-r", "155", text])
            elif shutil.which("espeak"):
                voice = "fr" if lang == "fr" else "en"
                self.fallback_proc = subprocess.Popen(["espeak", f"-v{voice}", "-s", "150", text])
        except Exception:
            pass

# -------------------------------------------------------------
# LOCALIZATION (EN / FR)
# -------------------------------------------------------------
TRANSLATIONS = {
    "en": {
        "level": "LEVEL {n}",
        "score": "SCORE",
        "enter_school": "Press (A) or SPACE to Enter English School!",
        "school_already_done": "English School is already completed!",
        "what_is": "What is {a} + {b}?",
        "what_is_spoken": "What is {a} plus {b}?",
        "stack_prompt": "Let's stack it in columns to solve it!",
        "btn_stack": "Press (A) or SPACE to stack columns",
        "unit_prompt": "First, add the units column to the right!",
        "btn_start_add": "Press (A) or SPACE to start adding",
        "carry_prompt": "Walk and push the 1 up to the tens box!",
        "tens_prompt": "Awesome! Now add the tens column.",
        "correct": "Correct! {a} + {b} = {ans} (+500 pts)",
        "correct_spoken": "Correct! {a} plus {b} equals {ans}!",
        "try_units": "Try again! Add the yellow units column.",
        "try_tens": "Try again! Add all tens (and carried box).",
        "class_dismissed": "School Complete! Returning to Maze...",
        "quota": "Class Goal: {n} sums left",
        "objective_hud": "Gems: {gems} left | Schools: [FR: {fr}] [EN: {en}]",
        "level2_spoken": "Bravo Pippa! You finished Level 1! Welcome to Level 2!",
    },
    "fr": {
        "level": "NIVEAU {n}",
        "score": "SCORE",
        "enter_school": "Appuie sur (A) ou ESPACE pour entrer à l'École !",
        "school_already_done": "L'École française est déjà terminée !",
        "what_is": "Combien font {a} + {b} ?",
        "what_is_spoken": "Combien font {a} plus {b} ?",
        "stack_prompt": "Posons l'addition en colonnes !",
        "btn_stack": "Appuie sur (A) ou ESPACE pour aligner",
        "unit_prompt": "D'abord, calcule les unités à la droite!",
        "btn_start_add": "Appuie sur (A) ou ESPACE pour commencer",
        "carry_prompt": "Pousse le 1 vers la boîte des dizaines !",
        "tens_prompt": "Bravo ! Maintenant, calcule les dizaines.",
        "correct": "Bravo ! {a} + {b} = {ans} (+500 pts)",
        "correct_spoken": "Bravo ! {a} plus {b} est égal à {ans} !",
        "try_units": "Essaie encore ! Additionne les unités en jaune.",
        "try_tens": "Essaie encore ! Additionne toutes les dizaines.",
        "class_dismissed": "Bravo ! Fin des cours, retour au village...",
        "quota": "Objectif : encore {n} calculs",
        "objective_hud": "Gemmes : {gems} | Écoles : [FR : {fr}] [EN : {en}]",
        "level2_spoken": "Bravo Pippa ! Tu as terminé le Niveau 1 ! Bienvenue au Niveau 2 !",
    }
}

def t(key, lang="en", **kwargs):
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    return text.format(**kwargs) if kwargs else text

# -------------------------------------------------------------
# GAME DIRECTOR (PERSISTENT STATE & DATA-DRIVEN LEVEL LOADER)
# -------------------------------------------------------------
class GameDirector:
    def __init__(self, character_name="mario"):
        self.score = 0
        self.language = "en"
        self.last_school = "en"
        # Cross-platform Y-axis polarity compensation
        self.y_mult = -1.0 if sys.platform == "darwin" else 1.0
        
        self.sfx = SoundFX()
        self.speech = SmartSpeechEngine()
        self.controller = None
        self.controller_centered = False  # Guard against startup ghost input
        self.init_controller()
       
        self.digit_w, self.digit_h = FONT_BIG.size("1")
        self.math_player_sprite = load_character_sprite(character_name, target_height=self.digit_h)
        self.maze_player_sprite = load_character_sprite(character_name, target_height=34)
        
        try:
            self.mazes = load_mazes("mazes.txt")
        except Exception as e:
            print(f"Warning: Could not read mazes.txt ({e}). Using default maze.")
            self.mazes = {"MAZE_A": DEFAULT_MAZE}

        self.current_level = 1
        self.maze_scene = None
        self.classroom_scene = None
        self.active_scene = None
        
        self.load_level(self.current_level)

    def init_controller(self):
        self.controller_centered = False
        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            print(f"Connected: {self.controller.get_name()}")
        else:
            self.controller = None

    def handle_global_event(self, event):
        if event.type == pygame.JOYDEVICEADDED:
            self.init_controller()
        elif event.type == pygame.JOYDEVICEREMOVED:
            self.controller = None
            self.controller_centered = False

    def load_level(self, level_num):
        self.current_level = level_num
        self.school_en_done = False
        self.school_fr_done = False

        cfg = LEVELS.get(level_num)
        if not cfg:
            self.active_scene = Level2Scene(self)
            return

        maze_id = cfg.get("maze_id", "MAZE_A")
        layout = self.mazes.get(maze_id, DEFAULT_MAZE)
        self.maze_scene = MazeScene(self, layout)
        self.classroom_scene = None
        self.active_scene = self.maze_scene

    def get_movement_vector(self, speed=5):
        move_x, move_y = 0.0, 0.0

        if self.controller:
            lx = self.controller.get_axis(0)
            ly = self.y_mult * self.controller.get_axis(1)

            rx, ry = 0.0, 0.0
            num_axes = self.controller.get_numaxes()
            if num_axes == 4:
                rx = self.controller.get_axis(2)
                ry = self.y_mult * self.controller.get_axis(3)
            elif num_axes >= 5:
                rx = self.controller.get_axis(3)
                ry = self.y_mult * self.controller.get_axis(4)

            # Wait until the controller reports a genuine neutral position before applying input
            if not self.controller_centered:
                if abs(lx) < 0.2 and abs(ly) < 0.2 and abs(rx) < 0.2 and abs(ry) < 0.2:
                    self.controller_centered = True
                else:
                    lx, ly, rx, ry = 0.0, 0.0, 0.0, 0.0

            l_mag = abs(lx) + abs(ly)
            r_mag = abs(rx) + abs(ry)

            if r_mag > l_mag and r_mag > 0.2:
                move_x += rx * speed
                move_y += ry * speed
            elif l_mag > 0.2:
                move_x += lx * speed
                move_y += ly * speed

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x = -speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x = speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_y = -speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y = speed

        return move_x, move_y

    def get_stick_vertical(self):
        if not self.controller or not self.controller_centered:
            return 0.0

        ly = self.y_mult * self.controller.get_axis(1)
        ry = 0.0
        num_axes = self.controller.get_numaxes()
        if num_axes == 4:
            ry = self.y_mult * self.controller.get_axis(3)
        elif num_axes >= 5:
            ry = self.y_mult * self.controller.get_axis(4)

        if abs(ry) > abs(ly):
            return ry
        return ly

    def enter_school(self, language="en"):
        self.speech.stop()
        self.language = language
        self.last_school = language
        
        cfg = LEVELS.get(self.current_level, LEVELS[1])
        quota = cfg.get("challenges_per_school", 5)
        
        self.classroom_scene = ClassroomScene(self, total_challenges=quota)
        self.active_scene = self.classroom_scene

    def exit_school(self):
        self.speech.stop()
        if self.last_school == "fr":
            self.school_fr_done = True
        elif self.last_school == "en":
            self.school_en_done = True

        if self.school_fr_done and self.school_en_done and len(self.maze_scene.gems) == 0:
            self.advance_to_level_2()
        else:
            self.maze_scene.reset_after_school(self.last_school)
            self.active_scene = self.maze_scene

    def advance_to_level_2(self):
        self.speech.stop()
        self.sfx.play_level_up()
        next_level = self.current_level + 1
        if next_level in LEVELS:
            self.load_level(next_level)
        else:
            self.current_level = 2
            self.active_scene = Level2Scene(self)

# -------------------------------------------------------------
# SCENE 1: THE MAZE / OVERWORLD (DATA-DRIVEN)
# -------------------------------------------------------------
class MazeScene:
    def __init__(self, director, layout=None):
        self.director = director
        self.tile_size = 50
        self.layout = layout if layout else DEFAULT_MAZE
        
        self.walls = []
        self.gems = []
        self.school_fr_rect = None
        self.school_en_rect = None
        self.hovered_school = None
        
        self.player_rect = pygame.Rect(0, 0, 24, 28)
        self.speed = 5
        self.load_map()

    def load_map(self):
        self.walls.clear()
        self.gems.clear()
        gem_colors = [COLOR_RUBY, COLOR_EMERALD, COLOR_DIAMOND]
        
        for r_idx, row in enumerate(self.layout):
            for c_idx, ch in enumerate(row):
                x = c_idx * self.tile_size
                y = r_idx * self.tile_size + 75
                if ch == "#":
                    self.walls.append(pygame.Rect(x, y, self.tile_size, self.tile_size))
                elif ch == ".":
                    self.gems.append({
                        "rect": pygame.Rect(x + 18, y + 18, 14, 14),
                        "color": random.choice(gem_colors)
                    })
                elif ch == "F":
                    self.school_fr_rect = pygame.Rect(x, y, self.tile_size * 2, self.tile_size)
                elif ch == "E":
                    self.school_en_rect = pygame.Rect(x - self.tile_size, y, self.tile_size * 2, self.tile_size)
                elif ch == "P":
                    self.player_rect.center = (x + self.tile_size // 2, y + self.tile_size // 2)

    def reset_after_school(self, school_lang):
        if school_lang == "fr":
            self.player_rect.x = self.school_fr_rect.right + 10
            self.player_rect.y = self.school_fr_rect.y + 10
        else:
            self.player_rect.x = self.school_en_rect.left - 35
            self.player_rect.y = self.school_en_rect.y + 10
        self.hovered_school = None

    def handle_event(self, event):
        if event.type == pygame.JOYBUTTONDOWN and event.button in (0, 1):
            self.try_enter_school()
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            self.try_enter_school()

    def try_enter_school(self):
        if self.player_rect.colliderect(self.school_fr_rect):
            if not self.director.school_fr_done:
                self.director.enter_school("fr")
            else:
                self.director.sfx.play_buzz()
        elif self.player_rect.colliderect(self.school_en_rect):
            if not self.director.school_en_done:
                self.director.enter_school("en")
            else:
                self.director.sfx.play_buzz()

    def update(self):
        move_x, move_y = self.director.get_movement_vector(self.speed)

        # X Collision
        self.player_rect.x += int(move_x)
        for wall in self.walls:
            if self.player_rect.colliderect(wall):
                if move_x > 0: self.player_rect.right = wall.left
                elif move_x < 0: self.player_rect.left = wall.right

        # Y Collision
        self.player_rect.y += int(move_y)
        for wall in self.walls:
            if self.player_rect.colliderect(wall):
                if move_y > 0: self.player_rect.bottom = wall.top
                elif move_y < 0: self.player_rect.top = wall.bottom

        # Cap movement on outer edge of schools
        if self.school_fr_rect and self.player_rect.colliderect(self.school_fr_rect):
            if self.player_rect.left < self.school_fr_rect.left:
                self.player_rect.left = self.school_fr_rect.left

        if self.school_en_rect and self.player_rect.colliderect(self.school_en_rect):
            if self.player_rect.right > self.school_en_rect.right:
                self.player_rect.right = self.school_en_rect.right

        # Perimeter clamp keeping Mario inside maze boundary
        self.player_rect.left = max(0, self.player_rect.left)
        self.player_rect.right = min(WIDTH, self.player_rect.right)
        self.player_rect.top = max(75, self.player_rect.top)
        self.player_rect.bottom = min(HEIGHT, self.player_rect.bottom)

        # Gem Pickups
        for gem in self.gems[:]:
            if self.player_rect.colliderect(gem["rect"]):
                self.gems.remove(gem)
                self.director.score += 5
                self.director.sfx.play_gem()

                if len(self.gems) == 0 and self.director.school_fr_done and self.director.school_en_done:
                    self.director.advance_to_level_2()
                    return

        # School Proximity Voice Prompt
        current_contact = None
        if self.player_rect.colliderect(self.school_fr_rect):
            current_contact = "fr"
        elif self.player_rect.colliderect(self.school_en_rect):
            current_contact = "en"

        if current_contact and current_contact != self.hovered_school:
            is_done = self.director.school_fr_done if current_contact == "fr" else self.director.school_en_done
            if is_done:
                self.director.speech.speak(t("school_already_done", current_contact), lang=current_contact)
            else:
                self.director.speech.speak(t("enter_school", current_contact), lang=current_contact)
        self.hovered_school = current_contact

    def draw(self, surface):
        surface.fill(BG_COLOR)
        
        for wall in self.walls:
            pygame.draw.rect(surface, COLOR_WALL, wall, border_radius=4)
            pygame.draw.rect(surface, (60, 70, 95), wall, width=1, border_radius=4)

        for gem in self.gems:
            pygame.draw.rect(surface, gem["color"], gem["rect"], border_radius=3)

        # French School (Left Door)
        fr_color = COLOR_SCHOOL_DONE if self.director.school_fr_done else COLOR_FR_SCHOOL
        pygame.draw.rect(surface, fr_color, self.school_fr_rect, border_radius=6)
        fr_label = "ECOLE (OK)" if self.director.school_fr_done else "ECOLE (FR)"
        fr_txt = FONT_SMALL.render(fr_label, True, COLOR_TEXT_LIT)
        surface.blit(fr_txt, fr_txt.get_rect(center=self.school_fr_rect.center))

        # English School (Right Door)
        en_color = COLOR_SCHOOL_DONE if self.director.school_en_done else COLOR_EN_SCHOOL
        pygame.draw.rect(surface, en_color, self.school_en_rect, border_radius=6)
        en_label = "SCHOOL (OK)" if self.director.school_en_done else "SCHOOL (EN)"
        en_txt = FONT_SMALL.render(en_label, True, COLOR_TEXT_LIT)
        surface.blit(en_txt, en_txt.get_rect(center=self.school_en_rect.center))

        sprite_rect = self.director.maze_player_sprite.get_rect(center=self.player_rect.center)
        surface.blit(self.director.maze_player_sprite, sprite_rect)

        if self.player_rect.colliderect(self.school_fr_rect):
            msg = t("school_already_done", "fr") if self.director.school_fr_done else t("enter_school", "fr")
            p_surf = FONT_MED.render(msg, True, COLOR_ACCENT if not self.director.school_fr_done else COLOR_TEXT_DIM)
            surface.blit(p_surf, p_surf.get_rect(center=(WIDTH // 2, HEIGHT - 35)))
        elif self.player_rect.colliderect(self.school_en_rect):
            msg = t("school_already_done", "en") if self.director.school_en_done else t("enter_school", "en")
            p_surf = FONT_MED.render(msg, True, COLOR_ACCENT if not self.director.school_en_done else COLOR_TEXT_DIM)
            surface.blit(p_surf, p_surf.get_rect(center=(WIDTH // 2, HEIGHT - 35)))

# -------------------------------------------------------------
# SCENE 2: CLASSROOM MATH (DATA-DRIVEN DIFFICULTY)
# -------------------------------------------------------------
STATE_INTRO_HORIZONTAL = 0
STATE_INTRO_STACKED = 1
STATE_GUESS_UNITS = 2
STATE_CARRY_BLOCK = 3
STATE_GUESS_TENS = 4
STATE_SUCCESS = 5
STATE_DISMISSED = 6

class ClassroomScene:
    def __init__(self, director, total_challenges=5):
        self.director = director
        self.remaining_challenges = total_challenges
        self.state = STATE_INTRO_HORIZONTAL
        
        self.feedback_msg = ""
        self.feedback_timer = 0
        self.success_timer = 0
        self.stick_cooldown = 0
        self.stick_neutral = True
        self.tens_started = False
        
        self.digit_w = self.director.digit_w
        self.digit_h = self.director.digit_h
        self.player_rect = pygame.Rect(150, 450, self.digit_w, self.digit_h)
        self.speed = 5
        
        self.tens_x = 420
        self.units_x = 490
        self.row1_y = 170
        self.row2_y = 250
        self.answer_y = 355
        
        self.tile_w = self.digit_w + 18
        self.tile_h = self.digit_h + 8
        self.carry_slot = pygame.Rect(self.tens_x - 14, 75, self.tile_w + 10, self.tile_h + 10)
        
        self.carry_block = None
        self.carry_placed = False

        self.spawn_new_problem()

    def spawn_new_problem(self):
        cfg = LEVELS.get(self.director.current_level, LEVELS[1])
        r1 = cfg.get("num1_range", (10, 19))
        r2 = cfg.get("num2_range", (4, 19))

        self.num1 = random.randint(r1[0], r1[1])
        self.num2 = random.randint(r2[0], r2[1])
        
        self.u1, self.t1 = self.num1 % 10, self.num1 // 10
        self.u2, self.t2 = self.num2 % 10, self.num2 // 10
        self.actual_unit_sum = self.u1 + self.u2
        
        self.has_tens_column = (self.t1 + self.t2 > 0)
        self.needs_carry = (self.actual_unit_sum > 9) and self.has_tens_column
        self.actual_tens_sum = self.t1 + self.t2 + (1 if self.needs_carry else 0)
        
        self.unit_guess = 0
        self.tens_guess = 0
        self.tens_started = False
        self.stick_neutral = True
        self.carry_block = None
        self.carry_placed = False
        self.feedback_msg = ""
        
        self.player_rect.topleft = (150, 450)
        self.state = STATE_INTRO_HORIZONTAL
        
        lang = self.director.language
        question_speech = t("what_is_spoken", lang, a=self.num1, b=self.num2)
        self.director.speech.speak(question_speech, lang=lang)

    def change_guess(self, delta):
        if self.state == STATE_GUESS_UNITS:
            self.unit_guess = max(0, min(19, self.unit_guess + delta))
        elif self.state == STATE_GUESS_TENS:
            if not self.tens_started:
                self.tens_started = True
                self.tens_guess = 1 if delta > 0 else 0
            else:
                self.tens_guess = max(0, min(9, self.tens_guess + delta))

    def handle_event(self, event):
        if (event.type == pygame.JOYBUTTONDOWN and event.button in (0, 1, 7)) or \
           (event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)):
            if self.state == STATE_SUCCESS and self.success_timer <= 60:
                if self.remaining_challenges > 0:
                    self.spawn_new_problem()
                else:
                    self.state = STATE_DISMISSED
                    self.feedback_msg = t("class_dismissed", self.director.language)
                    self.director.speech.speak(self.feedback_msg, lang=self.director.language)
                    self.success_timer = 90
                return
            elif self.state == STATE_DISMISSED:
                self.director.exit_school()
                return
            else:
                self.commit_action()
                return

        if event.type == pygame.JOYHATMOTION:
            if event.value[1] == 1: self.change_guess(1)
            elif event.value[1] == -1: self.change_guess(-1)

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.change_guess(1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.change_guess(-1)

    def commit_action(self):
        lang = self.director.language
        if self.state == STATE_INTRO_HORIZONTAL:
            self.state = STATE_INTRO_STACKED
            self.director.speech.speak(t("unit_prompt", lang), lang=lang)

        elif self.state == STATE_INTRO_STACKED:
            self.state = STATE_GUESS_UNITS

        elif self.state == STATE_GUESS_UNITS:
            if self.unit_guess == self.actual_unit_sum:
                if not self.has_tens_column:
                    self.award_success()
                elif self.needs_carry:
                    spawn_x = self.units_x - 35 - 9
                    spawn_y = self.answer_y - 4
                    self.carry_block = pygame.Rect(spawn_x, spawn_y, self.tile_w, self.tile_h)
                    self.state = STATE_CARRY_BLOCK
                    self.feedback_msg = t("carry_prompt", lang)
                    self.director.speech.speak(self.feedback_msg, lang=lang)
                else:
                    self.state = STATE_GUESS_TENS
                    self.tens_started = False
                    self.stick_neutral = False
                    self.feedback_msg = ""
            else:
                self.director.sfx.play_buzz()
                self.feedback_msg = t("try_units", lang)
                self.feedback_timer = 60
                self.director.speech.speak(self.feedback_msg, lang=lang)

        elif self.state == STATE_GUESS_TENS:
            if not self.tens_started: return
            if self.tens_guess == self.actual_tens_sum:
                self.award_success()
            else:
                self.director.sfx.play_buzz()
                self.feedback_msg = t("try_tens", lang)
                self.feedback_timer = 60
                self.director.speech.speak(self.feedback_msg, lang=lang)

    def award_success(self):
        self.state = STATE_SUCCESS
        self.director.score += 500
        self.director.sfx.play_success()
        self.remaining_challenges -= 1
        
        ans = self.num1 + self.num2
        lang = self.director.language
        self.feedback_msg = t("correct", lang, a=self.num1, b=self.num2, ans=ans)
        self.success_timer = 90
        
        spoken_ans = t("correct_spoken", lang, a=self.num1, b=self.num2, ans=ans)
        self.director.speech.speak(spoken_ans, lang=lang)

    def update(self):
        if self.state == STATE_SUCCESS:
            self.success_timer -= 1
            if self.success_timer <= 0 and not self.director.speech.is_busy():
                if self.remaining_challenges > 0:
                    self.spawn_new_problem()
                else:
                    self.state = STATE_DISMISSED
                    self.feedback_msg = t("class_dismissed", self.director.language)
                    self.director.speech.speak(self.feedback_msg, lang=self.director.language)
                    self.success_timer = 90
            elif self.success_timer <= -360:
                if self.remaining_challenges > 0:
                    self.spawn_new_problem()
                else:
                    self.state = STATE_DISMISSED
                    self.feedback_msg = t("class_dismissed", self.director.language)
                    self.director.speech.speak(self.feedback_msg, lang=self.director.language)
                    self.success_timer = 90
            return

        if self.state == STATE_DISMISSED:
            self.success_timer -= 1
            if (self.success_timer <= 0 and not self.director.speech.is_busy()) or self.success_timer <= -300:
                self.director.exit_school()
            return

        if self.state in (STATE_INTRO_HORIZONTAL, STATE_INTRO_STACKED):
            return

        vert = self.director.get_stick_vertical()

        if self.state == STATE_GUESS_UNITS:
            if self.stick_cooldown > 0:
                self.stick_cooldown -= 1
            else:
                if vert < -0.5:
                    self.change_guess(1)
                    self.stick_cooldown = 14
                elif vert > 0.5:
                    self.change_guess(-1)
                    self.stick_cooldown = 14

        elif self.state == STATE_GUESS_TENS:
            if not self.stick_neutral:
                if abs(vert) < 0.2: self.stick_neutral = True
            else:
                if self.stick_cooldown > 0:
                    self.stick_cooldown -= 1
                else:
                    if vert < -0.5:
                        self.change_guess(1)
                        self.stick_cooldown = 14
                    elif vert > 0.5:
                        self.change_guess(-1)
                        self.stick_cooldown = 14

        # Carry Locomotion with screen boundary clamps for the carry block
        if self.state == STATE_CARRY_BLOCK:
            move_x, move_y = self.director.get_movement_vector(self.speed)

            new_x = max(0, min(WIDTH - self.player_rect.width, self.player_rect.x + int(move_x)))
            new_y = max(0, min(HEIGHT - self.player_rect.height, self.player_rect.y + int(move_y)))

            if self.carry_block and not self.carry_placed:
                future_rect = pygame.Rect(new_x, new_y, self.player_rect.width, self.player_rect.height)
                if future_rect.colliderect(self.carry_block):
                    push_dx = new_x - self.player_rect.x
                    push_dy = new_y - self.player_rect.y

                    target_bx = self.carry_block.x + push_dx
                    target_by = self.carry_block.y + push_dy

                    # Safe screen boundaries keeping a corridor for Mario to walk around
                    min_bx = 60
                    max_bx = WIDTH - self.carry_block.width - 60
                    min_by = 70
                    max_by = HEIGHT - self.carry_block.height - 60

                    clamped_bx = max(min_bx, min(max_bx, target_bx))
                    clamped_by = max(min_by, min(max_by, target_by))

                    # If block hits a boundary, stop Mario from walking through it
                    if clamped_bx != target_bx:
                        if push_dx > 0:
                            new_x = clamped_bx - self.player_rect.width
                        elif push_dx < 0:
                            new_x = clamped_bx + self.carry_block.width

                    if clamped_by != target_by:
                        if push_dy > 0:
                            new_y = clamped_by - self.player_rect.height
                        elif push_dy < 0:
                            new_y = clamped_by + self.carry_block.height

                    self.carry_block.x = clamped_bx
                    self.carry_block.y = clamped_by

                    if self.carry_slot.contains(self.carry_block) or self.carry_slot.colliderect(self.carry_block):
                        self.carry_block.center = self.carry_slot.center
                        self.carry_placed = True
                        self.state = STATE_GUESS_TENS
                        self.tens_started = False
                        self.stick_neutral = False
                        self.stick_cooldown = 20
                        
                        lang = self.director.language
                        self.feedback_msg = t("tens_prompt", lang)
                        self.director.speech.speak(self.feedback_msg, lang=lang)
                        new_x, new_y = 150, 450

            self.player_rect.x = new_x
            self.player_rect.y = new_y

        if self.feedback_timer > 0:
            self.feedback_timer -= 1
            if self.feedback_timer == 0: self.feedback_msg = ""

    def draw(self, surface):
        surface.fill(BG_COLOR)
        lang = self.director.language

        quota_txt = FONT_SMALL.render(t("quota", lang, n=self.remaining_challenges), True, COLOR_TARGET)
        surface.blit(quota_txt, (WIDTH - 240, 55))

        if self.state == STATE_INTRO_HORIZONTAL:
            q_surf = FONT_BIG.render(t("what_is", lang, a=self.num1, b=self.num2), True, COLOR_ACCENT)
            surface.blit(q_surf, q_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            
            sub_surf = FONT_MED.render(t("stack_prompt", lang), True, COLOR_TEXT_LIT)
            surface.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))
            
            btn_hint = FONT_MED.render(t("btn_stack", lang), True, COLOR_SUCCESS)
            surface.blit(btn_hint, btn_hint.get_rect(center=(WIDTH // 2, HEIGHT - 80)))
            return

        if self.has_tens_column:
            pygame.draw.rect(surface, (45, 50, 70), self.carry_slot, border_radius=8)
            pygame.draw.rect(surface, COLOR_TARGET, self.carry_slot, width=2, border_radius=8)
            if self.carry_placed:
                carry_txt = FONT_BIG.render("1", True, COLOR_ACCENT)
                surface.blit(carry_txt, carry_txt.get_rect(center=self.carry_slot.center))

        tens_color = COLOR_TEXT_LIT if self.state in (STATE_INTRO_STACKED, STATE_CARRY_BLOCK, STATE_SUCCESS) else (
            COLOR_ACCENT if self.state == STATE_GUESS_TENS else COLOR_TEXT_DIM)
        units_color = COLOR_ACCENT if self.state == STATE_GUESS_UNITS else COLOR_TEXT_LIT

        surface.blit(FONT_BIG.render(str(self.t1 if self.t1 > 0 else ' '), True, tens_color), (self.tens_x, self.row1_y))
        surface.blit(FONT_BIG.render(str(self.u1), True, units_color), (self.units_x, self.row1_y))
        surface.blit(FONT_BIG.render("+", True, COLOR_TEXT_LIT), (self.tens_x - 60, self.row2_y))
        surface.blit(FONT_BIG.render(str(self.t2 if self.t2 > 0 else ' '), True, tens_color), (self.tens_x, self.row2_y))
        surface.blit(FONT_BIG.render(str(self.u2), True, units_color), (self.units_x, self.row2_y))
        pygame.draw.line(surface, COLOR_TEXT_LIT, (self.tens_x - 60, self.row2_y + 80), (self.units_x + 50, self.row2_y + 80), 4)

        if self.state == STATE_INTRO_STACKED:
            p_surf = FONT_MED.render(t("unit_prompt", lang), True, COLOR_ACCENT)
            surface.blit(p_surf, p_surf.get_rect(center=(WIDTH // 2, 470)))
            btn_hint = FONT_MED.render(t("btn_start_add", lang), True, COLOR_SUCCESS)
            surface.blit(btn_hint, btn_hint.get_rect(center=(WIDTH // 2, HEIGHT - 80)))
            return

        if self.state == STATE_GUESS_UNITS:
            surface.blit(FONT_BIG.render(f"{self.unit_guess:02d}", True, COLOR_ACCENT), (self.units_x - 35, self.answer_y))
        elif self.state == STATE_CARRY_BLOCK:
            surface.blit(FONT_BIG.render(str(self.actual_unit_sum % 10), True, COLOR_TEXT_LIT), (self.units_x, self.answer_y))
        elif self.state in (STATE_GUESS_TENS, STATE_SUCCESS):
            surface.blit(FONT_BIG.render(str(self.actual_unit_sum % 10), True, COLOR_TEXT_LIT), (self.units_x, self.answer_y))
            if self.state == STATE_SUCCESS:
                tens_val = self.actual_tens_sum if self.has_tens_column else (self.actual_unit_sum // 10)
                if tens_val > 0:
                    surface.blit(FONT_BIG.render(str(tens_val), True, tens_color), (self.tens_x, self.answer_y))
            elif self.state == STATE_GUESS_TENS and self.tens_started:
                surface.blit(FONT_BIG.render(str(self.tens_guess), True, tens_color), (self.tens_x, self.answer_y))

        if self.state == STATE_CARRY_BLOCK and self.carry_block and not self.carry_placed:
            pygame.draw.rect(surface, (45, 50, 70), self.carry_block, border_radius=8)
            pygame.draw.rect(surface, COLOR_ACCENT, self.carry_block, width=2, border_radius=8)
            b_txt = FONT_BIG.render("1", True, COLOR_ACCENT)
            surface.blit(b_txt, b_txt.get_rect(center=self.carry_block.center))

        surface.blit(self.director.math_player_sprite, self.player_rect)

        if self.feedback_msg:
            color = COLOR_FEEDBACK if ("Try" in self.feedback_msg or "Essaie" in self.feedback_msg) else COLOR_SUCCESS
            f_surf = FONT_MED.render(self.feedback_msg, True, color)
            surface.blit(f_surf, f_surf.get_rect(center=(WIDTH // 2, 580)))

# -------------------------------------------------------------
# SCENE 3: LEVEL 2 SHOWCASE (INTERIM TRANSITION)
# -------------------------------------------------------------
class Level2Scene:
    def __init__(self, director):
        self.director = director
        self.announced = False
        self.stars = [
            (random.randint(40, WIDTH - 40), random.randint(100, HEIGHT - 100), random.choice([COLOR_ACCENT, COLOR_DIAMOND, COLOR_EMERALD]))
            for _ in range(40)
        ]

    def handle_event(self, event):
        pass

    def update(self):
        if not self.announced:
            self.announced = True
            lang = self.director.language
            self.director.speech.speak(t("level2_spoken", lang), lang=lang)

    def draw(self, surface):
        surface.fill(BG_COLOR)

        for (sx, sy, col) in self.stars:
            pygame.draw.circle(surface, col, (sx, sy), 3)

        t_surf = FONT_BIG.render(t("level", self.director.language, n=2), True, COLOR_ACCENT)
        surface.blit(t_surf, t_surf.get_rect(center=(WIDTH // 2, 170)))

        c_surf = FONT_MED.render("CONGRATULATIONS PIPPA!", True, COLOR_SUCCESS)
        surface.blit(c_surf, c_surf.get_rect(center=(WIDTH // 2, 250)))

        m1 = FONT_SMALL.render("You collected all the gems and graduated from both schools!", True, COLOR_TEXT_LIT)
        surface.blit(m1, m1.get_rect(center=(WIDTH // 2, 305)))

        sprite_rect = self.director.math_player_sprite.get_rect(center=(WIDTH // 2, 400))
        surface.blit(self.director.math_player_sprite, sprite_rect)

        m2 = FONT_MED.render("Level 2 adventures coming soon...", True, COLOR_TARGET)
        surface.blit(m2, m2.get_rect(center=(WIDTH // 2, 510)))

# -------------------------------------------------------------
# GLOBAL HUD
# -------------------------------------------------------------
def draw_persistent_hud(surface, director):
    pygame.draw.rect(surface, (18, 20, 28), (0, 0, WIDTH, 50))
    pygame.draw.line(surface, (45, 52, 70), (0, 50), (WIDTH, 50), 2)
    
    # Level & Score Banner
    lvl_str = t("level", director.language, n=director.current_level)
    hud_left = f"{lvl_str}  |  {t('score', director.language)}: {director.score:05d}"
    surface.blit(FONT_MED.render(hud_left, True, COLOR_ACCENT), (20, 10))
    
    # Objective Tracker in Maze
    if isinstance(director.active_scene, MazeScene):
        fr_tag = "OK" if director.school_fr_done else "--"
        en_tag = "OK" if director.school_en_done else "--"
        obj_txt = t("objective_hud", director.language, gems=len(director.active_scene.gems), fr=fr_tag, en=en_tag)
        surface.blit(FONT_SMALL.render(obj_txt, True, COLOR_TEXT_LIT), (WIDTH - 440, 16))

    lang_badge = f"[{director.language.upper()}]"
    surface.blit(FONT_SMALL.render(lang_badge, True, COLOR_TEXT_DIM), (WIDTH - 60, 16))

# -------------------------------------------------------------
# MAIN GAME LOOP
# -------------------------------------------------------------
if __name__ == '__main__':
    director = GameDirector("mario")

    while True:
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                director.speech.stop()
                pygame.quit()
                sys.exit()
            director.handle_global_event(event)
            director.active_scene.handle_event(event)

        director.active_scene.update()
        director.active_scene.draw(screen)
        draw_persistent_hud(screen, director)
        
        pygame.display.flip()
        clock.tick(60)