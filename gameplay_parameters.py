# gameplay_parameters.py

LEVELS = {
    1: {
        "title": "Level 1",
        "maze_id": "MAZE_A",
        "challenges_per_school": 4,
        "num1_range": (10, 19),
        "num2_range": (4, 19),
        "scene_type": "classroom",
    },
    2: {
        "title": "Level 2",
        "maze_id": "MAZE_B",
        "challenges_per_school": 4,
        "scene_type": "compare",
        "compare_mode": "operator",  # Level 2: Push the operator
    },
    3: {
        "title": "Level 3",
        "maze_id": "MAZE_C",
        "challenges_per_school": 4,
        "scene_type": "compare",
        "compare_mode": "adjust_number",  # Level 3: Adjust the missing number
    },
}

def load_mazes(filepath="mazes.txt"):
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