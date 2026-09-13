# Gameplay configuration per level
LEVELS = {
    1: {
        "title": "Level 1",
        "maze_id": "MAZE_A",
        "challenges_per_school": 4,
        "num1_range": (10, 19),
        "num2_range": (4, 19),
        "scene_type": "classroom",  # In the future: "space_station", "castle", etc.
    },
    2: {
        "title": "Level 2",
        "maze_id": "MAZE_B",
        "challenges_per_school": 4,
        "num1_range": (15, 29),      # Slightly larger two-digit addition
        "num2_range": (6, 29),
        "scene_type": "classroom",
    },
}

def load_mazes(filepath="mazes.txt"):
    """Parses text file with sections [MAZE_ID] into raw string grids."""
    mazes = {}
    current_maze = None
    
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                current_maze = stripped[1:-1]
                mazes[current_maze] = []
            elif current_maze:
                mazes[current_maze].append(stripped)
                
    return mazes