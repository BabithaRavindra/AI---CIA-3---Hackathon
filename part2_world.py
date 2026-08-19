"""
================================================================================
AURA: Autonomous Understanding & Replanning Agent
PIXAR WALL-E RECLAMATION DIRECTIVE

PART 2 of 3: WORLD / VISUAL CONSTANTS & SECTOR GENERATOR
--------------------------------------------------------------------------------
This is one of three files that together make up the original aihackathon1.py
program, split for readability. No functionality was changed or removed - see
aihackathon1_part1_logic.py for details and run aihackathon1_part3_gui.py to
start the application.

  Part 1               -> aihackathon1_part1_logic.py  : Propositional Logic KB
                                                          + Knowledge-Based Agent
  Part 2 (this file)  -> aihackathon1_part2_world.py  : Colors/dimensions
                                                          + Scrap world generator
  Part 3               -> aihackathon1_part3_gui.py    : Pygame GUI + entry point
================================================================================
"""

from typing import List

# -----------------------------------------------------------------------------
# 3. COLOR PALETTE & DIMENSIONS
# -----------------------------------------------------------------------------
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
GRID_SIZE = 20
GRID_PIXELS = 720
CELL_SIZE = GRID_PIXELS // GRID_SIZE
GRID_OFFSET_X = 30
GRID_OFFSET_Y = (WINDOW_HEIGHT - GRID_PIXELS) // 2

PANEL_X = GRID_OFFSET_X + GRID_PIXELS + 30
PANEL_WIDTH = WINDOW_WIDTH - PANEL_X - 30

COLOR_BG = (18, 14, 12)
COLOR_PANEL_BG = (28, 25, 23)
COLOR_PANEL_BORDER = (217, 119, 6)
COLOR_GRID_BG = (24, 20, 18)

# Obstacle Colors
COLOR_SCRAP_CUBE = (87, 83, 78)
COLOR_SCRAP_BORDER = (120, 113, 108)
COLOR_SECUR_T_BODY = (248, 250, 252)
COLOR_SECUR_T_EYE = (239, 68, 68)
COLOR_TOXIC_SLUDGE = (132, 204, 22)   # Neon Toxic Slime Green
COLOR_SLUDGE_DARK = (54, 83, 20)
COLOR_ENGINE_RUST = (180, 83, 9)      # Engine Block Rust
COLOR_ENGINE_DARK = (68, 64, 60)
COLOR_MO_WHITE = (241, 245, 249)      # M-O Bot White
COLOR_MO_BEACON = (249, 115, 22)      # M-O Orange Beacon

# Search Probing Lines
COLOR_PROBE_SAFE = (56, 189, 248)     # EVE Cyan Blue Line
COLOR_PROBE_COLLISION = (239, 68, 68) # Hazard Red Collision Line
COLOR_PATH_TRAIL = (250, 204, 21)     # Single Solid Gold Route
COLOR_TRAIL_VISITED = (14, 116, 144)  # Dimmer Cyan Visited Footprints

# WALL-E & Goal
COLOR_WALLE_YELLOW = (234, 153, 23)
COLOR_WALLE_TREADS = (41, 37, 36)
COLOR_WALLE_EYE_GLASS = (14, 165, 233)
COLOR_PLANT_GREEN = (34, 197, 94)
COLOR_BOOT_BROWN = (120, 53, 15)

# UI Text
COLOR_TEXT_PRIMARY = (254, 243, 199)
COLOR_TEXT_AMBER = (245, 158, 11)
COLOR_TEXT_CYAN = (56, 189, 248)
COLOR_TEXT_GREEN = (74, 222, 128)
COLOR_TEXT_RED = (248, 113, 113)
COLOR_BUTTON_HOVER = (68, 40, 15)
COLOR_BUTTON_ACTION = (22, 101, 52)


# -----------------------------------------------------------------------------
# 4. MULTI-OBSTACLE SCRAP WORLD GENERATOR (5 DISTINCT OBSTACLES)
# -----------------------------------------------------------------------------
class SectorManager:
    @staticmethod
    def generate_sector(style_idx: int, size: int) -> List[List[int]]:
        grid = [[0 for _ in range(size)] for _ in range(size)]

        for i in range(size):
            grid[0][i] = 1
            grid[size - 1][i] = 1
            grid[i][0] = 1
            grid[i][size - 1] = 1

        if style_idx % 3 == 0:
            for x in range(3, 7): grid[4][x] = 1; grid[15][x] = 1
            for x in range(13, 17): grid[4][x] = 1; grid[15][x] = 1
            for y in range(6, 14): grid[y][4] = 4; grid[y][15] = 4
            for x in range(8, 12): grid[8][x] = 1; grid[11][x] = 1

            grid[9][6] = 3; grid[10][6] = 3; grid[9][13] = 3; grid[10][13] = 3
            grid[6][9] = 2; grid[13][10] = 2
            grid[3][11] = 5; grid[16][8] = 5

        elif style_idx % 3 == 1:
            for col in (5, 9, 14):
                for row in range(2, 8): grid[row][col] = 1 if row % 2 == 0 else 4
                for row in range(12, 18): grid[row][col] = 1 if row % 2 == 0 else 4
            for x in range(6, 9): grid[9][x] = 3
            for x in range(10, 13): grid[10][x] = 3

            grid[7][7] = 2; grid[12][12] = 2
            grid[4][12] = 5; grid[15][7] = 5

        else:
            for y in range(3, 17, 3):
                for x in range(3, 17, 3):
                    grid[y][x] = 1
                    grid[y][x + 1] = 4
                    grid[y + 1][x] = 3

            grid[5][5] = 2; grid[14][14] = 2
            grid[8][11] = 5; grid[11][8] = 5

        grid[1][1] = 0; grid[1][2] = 0; grid[2][1] = 0
        grid[size - 2][size - 2] = 0
        grid[size - 2][size - 3] = 0
        grid[size - 3][size - 2] = 0

        return grid
