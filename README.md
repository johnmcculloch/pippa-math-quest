# Pippa & Mario: Math Quest

A modular, retro-style educational game designed to teach two-digit column addition with carrying, and other skills, directed at MCPS French Immersion Programme. Players explore maze overworlds, collect gems, and complete math challenges at bilingual English and French schools to progress through levels[cite: 3].

---

### Features

* **RPG Adventure Loop:** Navigate mazes, collect gem collectibles (+5 pts), and unlock English and French schools (+500 pts per sum)[cite: 3].
* **Kinesthetic Math:** Learn column addition hands-on by walking Mario to push the carried "1" into the tens column[cite: 3].
* **Bilingual Support (EN / FR):** Dedicated English School and French École entrances with spoken and visual prompts in both languages[cite: 3].
* **Offline Spoken Audio:** Natural human voice narration using `gTTS` with automatic offline caching in `voice_cache/`, falling back to native system speech (`say` or `espeak`)[cite: 3].
* **Ambidextrous Controls:** Full dual-stick gamepad support alongside an arrow/WASD keyboard fallback[cite: 3].
* **Data-Driven Architecture:** Level progression and maze layouts are separated into `gameplay_parameters.py` and `mazes.txt` for easy level creation without touching game code[cite: 3].

---

### Prerequisites & Installation

#### macOS

1. Open **Terminal**.
2. Verify Python 3 is installed:
   ```bash
   python3 --version
   ```
3. Install required Python packages:
   ```bash
   python3 -m pip install pygame-ce gTTS pyttsx3
   ```

#### Linux (Edubuntu / Ubuntu / Debian)

1. Open **Terminal**.
2. Install Python, pip, and audio dependencies:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-pygame espeak-ng libespeak1
   ```
3. Install the speech libraries via pip:
   ```bash
   python3 -m pip install gTTS pyttsx3
   ```
   *(Note: If your system uses externally managed environments, append `--break-system-packages` or install inside a Python virtual environment).*

---

### Running the Game

Clone the repository and launch the main loop[cite: 3]:

```bash
git clone https://github.com/johnmcculloch/pippa-math-quest.git
cd pippa-math-quest
python3 pippa_maths_retrogame.py
```

---

### Controls

| Action | Gamepad (Logitech / Xbox / PS)[cite: 3] | Keyboard Fallback[cite: 3] |
| :--- | :--- | :--- |
| **Move / Push Block**[cite: 3] | Left Stick OR Right Stick[cite: 3] | `W, A, S, D` or Arrow Keys[cite: 3] |
| **Cycle Number**[cite: 3] | Stick Up / Down or D-Pad[cite: 3] | `Up` / `Down` or `W` / `S`[cite: 3] |
| **Confirm / Enter School**[cite: 3] | `A` Button (Button 0 or 1)[cite: 3] | `Space` or `Enter`[cite: 3] |

---

### Level Customization

* **`mazes.txt`**: Define maze layouts using plain text[cite: 3]. Use `#` for walls, `.` for gems, `P` for the player start, `F` for École, and `E` for English School[cite: 3].
* **`gameplay_parameters.py`**: Configure problem ranges (`num1_range`, `num2_range`), question quotas per school, and which maze layout to load for each level[cite: 3].
