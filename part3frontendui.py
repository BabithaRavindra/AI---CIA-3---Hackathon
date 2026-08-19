"""
================================================================================
AURA: Autonomous Understanding & Replanning Agent
PIXAR WALL-E RECLAMATION DIRECTIVE
Stepped Path Search with Collision Backtracking & Multi-Obstacle Scrap World

PART 3 of 3: GUI ENGINE & ENTRY POINT
--------------------------------------------------------------------------------
This is one of three files that together make up the original aihackathon1.py
program, split for readability. No functionality was changed or removed - this
file wires together Part 1 (KB + Agent) and Part 2 (world/visual constants) and
runs the pygame application, exactly as the original single file did.

  Part 1               -> aihackathon1_part1_logic.py  : Propositional Logic KB
                                                          + Knowledge-Based Agent
  Part 2               -> aihackathon1_part2_world.py  : Colors/dimensions
                                                          + Scrap world generator
  Part 3 (this file)  -> aihackathon1_part3_gui.py    : Pygame GUI + entry point

Features:
  - 5 Distinct Obstacle Types:
      1. Compacted Trash Scrap Cube (Solid compressed scrap metal)
      2. Axiom Secur-T Drone (Red-eye patrol robot)
      3. Radioactive Toxic Sludge (Glowing biohazard slime pool)
      4. Crushed Vehicle Engine Frame (Jagged scrap wreckage)
      5. Axiom M-O Cleaner Bot (Microbe-Obliterator scrub drone)
  - Interactive [FIND PATH] Button:
      Watch the AI probe the grid step-by-step with live cyan search lines,
      turn RED on wall/hazard collisions, and backtrack dynamically.
  - Strictly Single True Yellow Route:
      Remaining path ahead is rendered as ONE contiguous golden line with zero
      diagonal jump lines.
  - Fully Scrollable Live Probing Terminal Feed:
      Mouse wheel scrolling, visual BnL scrollbar, and hardware text clipping
      (no text ever spills past boundaries).
  - Themed "ROUTE DISCOVERED!" Pop-up Modal when path search reaches the Plant.
  - Full Propositional Logic KB: PerceiveHazard(x,y) => not Move(x,y).

Run with:  python aihachekathon1_part3_gui.py
================================================================================
"""

import sys
import time
import math
from typing import List, Tuple, Set

import pygame

from aihackathon1_part1_logic import KnowledgeBasedAgent, Agent, TraceEvent
from aihackathon1_part2_world import (
    WINDOW_WIDTH, WINDOW_HEIGHT, GRID_SIZE, GRID_PIXELS, CELL_SIZE,
    GRID_OFFSET_X, GRID_OFFSET_Y, PANEL_X, PANEL_WIDTH,
    COLOR_BG, COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_GRID_BG,
    COLOR_SCRAP_CUBE, COLOR_SCRAP_BORDER, COLOR_SECUR_T_BODY, COLOR_SECUR_T_EYE,
    COLOR_TOXIC_SLUDGE, COLOR_SLUDGE_DARK, COLOR_ENGINE_RUST, COLOR_ENGINE_DARK,
    COLOR_MO_WHITE, COLOR_MO_BEACON,
    COLOR_PROBE_SAFE, COLOR_PROBE_COLLISION, COLOR_PATH_TRAIL, COLOR_TRAIL_VISITED,
    COLOR_WALLE_YELLOW, COLOR_WALLE_TREADS, COLOR_WALLE_EYE_GLASS, COLOR_PLANT_GREEN,
    COLOR_BOOT_BROWN,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_AMBER, COLOR_TEXT_CYAN, COLOR_TEXT_GREEN,
    COLOR_TEXT_RED, COLOR_BUTTON_HOVER, COLOR_BUTTON_ACTION,
    SectorManager,
)



# -----------------------------------------------------------------------------
# 5. GUI ENGINE WITH ACCURATE PATH & SCROLLABLE PROBING FEED
# -----------------------------------------------------------------------------
class AuraWalleStepGUI:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("AURA // WALL•E RECLAMATION (Live Stepped AI Path Search)")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("Impact, Arial Black, Segoe UI", 25)
        self.font_sub = pygame.font.SysFont("Impact, Arial Black, Segoe UI", 15)
        self.font_modal_title = pygame.font.SysFont("Impact, Arial Black, Segoe UI", 28)
        self.font_body = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13, bold=True)
        self.font_mono = pygame.font.SysFont("Consolas, Courier New, monospace", 11, bold=True)
        self.font_badge = pygame.font.SysFont("Impact, Segoe UI, sans-serif", 14)

        # Simulation Grid & Sector Manager
        self.sector_index = 0
        self.start_pos = (1, 1)
        self.goal_pos = (GRID_SIZE - 2, GRID_SIZE - 2)
        self.grid = SectorManager.generate_sector(self.sector_index, GRID_SIZE)

        # Agent Initialization
        self.agent = KnowledgeBasedAgent(start_pos=self.start_pos, goal_pos=self.goal_pos)

        # Stepped Search Animation State
        self.is_probing_path = False
        self.search_trace: List[TraceEvent] = []
        self.trace_idx = 0
        self.active_probe_segments: List[Tuple[Tuple[int, int], Tuple[int, int], bool]] = []
        self.visited_trail: List[Tuple[int, int]] = [self.start_pos]

        # Modals & UI states
        self.show_route_found_modal = False
        self.show_mission_complete_modal = False
        self.modal_btn_action = pygame.Rect(0, 0, 200, 44)
        self.modal_btn_dismiss = pygame.Rect(0, 0, 160, 44)

        # Buttons on Dashboard
        self.btn_find_path = pygame.Rect(PANEL_X + 20, 0, PANEL_WIDTH - 40, 42)
        self.btn_refresh = pygame.Rect(PANEL_X + 20, 0, PANEL_WIDTH - 40, 38)
        self.feed_box_rect = pygame.Rect(PANEL_X + 20, 0, PANEL_WIDTH - 40, 145)

        # Scrollable Log State
        self.log_scroll_pos = 0  # 0 = Scrolled to bottom, >0 = Scrolled up by N lines
        self.action_logs: List[str] = [
            "BNL AXIOM OS INITIALIZED.",
            f"DIRECTIVE: RECOVER SEEDLING AT {self.goal_pos}.",
            "CLICK [🔍 FIND PATH] TO WATCH STEP-BY-STEP AI SEARCH."
        ]

        # Simulation Loop State
        self.is_simulating = False
        self.step_delay = 0.12
        self.last_step_time = time.time()
        self.anim_timer = 0.0
        self.cleared_scrap: Set[Tuple[int, int]] = {self.start_pos}

        self.start_stepped_path_find()

    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        self.action_logs.append(f"[{timestamp}] {message.upper()}")
        if len(self.action_logs) > 500:
            self.action_logs.pop(0)

    def start_stepped_path_find(self):
        """Initiates real-time step-by-step search probing with backtracking visualization."""
        self.is_simulating = False
        self.show_route_found_modal = False
        self.show_mission_complete_modal = False
        self.visited_trail = [getattr(self.agent, "current_position", self.start_pos)]
        self.active_probe_segments.clear()
        self.log_scroll_pos = 0  # Snap scroll to bottom

        self.search_trace, final_path = self.agent.generate_search_trace(self.grid)
        self.trace_idx = 0
        self.is_probing_path = True
        self.log("INITIATING STEP-BY-STEP AI PROBING SCAN...")

    def refresh_sector(self):
        self.sector_index += 1
        self.grid = SectorManager.generate_sector(self.sector_index, GRID_SIZE)
        self.cleared_scrap = {self.start_pos}
        self.visited_trail = [self.start_pos]
        self.log_scroll_pos = 0
        self.agent.reset(self.grid)
        self.start_stepped_path_find()
        self.log(f"EARTH SECTOR #{self.sector_index + 1} LOADED.")

    def handle_click(self, pos: Tuple[int, int]):
        mx, my = pos

        # Route Found Modal Button Handlers
        if self.show_route_found_modal:
            if self.modal_btn_action.collidepoint(mx, my):
                self.show_route_found_modal = False
                self.is_simulating = True
                self.log("EXECUTING DIRECTIVE: WALL•E ROLLING!")
                return
            elif self.modal_btn_dismiss.collidepoint(mx, my):
                self.show_route_found_modal = False
                return

        # Mission Complete Modal Button Handlers
        if self.show_mission_complete_modal:
            if self.modal_btn_action.collidepoint(mx, my):
                self.show_mission_complete_modal = False
                self.refresh_sector()
                return
            elif self.modal_btn_dismiss.collidepoint(mx, my):
                self.show_mission_complete_modal = False
                self.reset_simulation()
                return

        # Dashboard Buttons
        if self.btn_find_path.collidepoint(mx, my):
            self.start_stepped_path_find()
            return
        elif self.btn_refresh.collidepoint(mx, my):
            self.refresh_sector()
            return

        # Click on Log Box to Scroll Up/Down
        if self.feed_box_rect.collidepoint(mx, my):
            if my < self.feed_box_rect.centery:
                self.log_scroll_pos = min(max(0, len(self.action_logs) - 6), self.log_scroll_pos + 3)
            else:
                self.log_scroll_pos = max(0, self.log_scroll_pos - 3)
            return

        # Grid Click: Cycle through Obstacle Types (0 -> 2 -> 3 -> 4 -> 5 -> 0)
        gx = (mx - GRID_OFFSET_X) // CELL_SIZE
        gy = (my - GRID_OFFSET_Y) // CELL_SIZE

        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
            curr_pos = getattr(self.agent, "current_position", self.start_pos)
            if (gx, gy) in (self.start_pos, self.goal_pos, curr_pos):
                return

            self.grid[gy][gx] = (self.grid[gy][gx] + 1) % 6
            if self.grid[gy][gx] == 1:
                self.grid[gy][gx] = 2

            obs_names = {0: "CLEARED", 2: "SECUR-T BOT", 3: "TOXIC SLUDGE", 4: "CRUSHED ENGINE", 5: "M-O CLEANER"}
            self.log(f"GRID ({gx},{gy}) SET TO: {obs_names.get(self.grid[gy][gx], 'OBSTACLE')}")
            self.start_stepped_path_find()

    def reset_simulation(self):
        self.cleared_scrap = {self.start_pos}
        self.visited_trail = [self.start_pos]
        self.show_route_found_modal = False
        self.show_mission_complete_modal = False
        self.log_scroll_pos = 0
        self.agent.reset(self.grid)
        self.start_stepped_path_find()
        self.log("WALL•E RETURNED TO BASE CAMP.")

    # -------------------------------------------------------------------------
    # SPRITE DRAWING HELPERS (5 DISTINCT OBSTACLE TYPES)
    # -------------------------------------------------------------------------
    def _draw_obstacle(self, rect: pygame.Rect, obs_type: int):
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        cx, cy = rect.center
        inner = rect.inflate(-4, -4)

        if obs_type == 1:
            pygame.draw.rect(self.screen, COLOR_SCRAP_CUBE, inner, border_radius=3)
            pygame.draw.rect(self.screen, COLOR_SCRAP_BORDER, inner, 2, border_radius=3)
            pygame.draw.line(self.screen, (154, 52, 18), (inner.left + 3, cy), (inner.right - 3, cy), 2)
            pygame.draw.circle(self.screen, (200, 200, 200), (inner.left + 3, inner.top + 3), 1)

        elif obs_type == 2:
            pygame.draw.ellipse(self.screen, COLOR_SECUR_T_BODY, inner)
            pygame.draw.ellipse(self.screen, (203, 213, 225), inner, 2)
            pulse = abs(math.sin(self.anim_timer * 8)) * 2
            pygame.draw.circle(self.screen, (60, 0, 0), (cx, cy), 6)
            pygame.draw.circle(self.screen, COLOR_SECUR_T_EYE, (cx, cy), int(3 + pulse))
            if int(self.anim_timer * 6) % 2 == 0:
                pygame.draw.line(self.screen, (239, 68, 68), (cx - 4, y + 2), (cx + 4, y + 2), 2)

        elif obs_type == 3:
            pygame.draw.ellipse(self.screen, COLOR_SLUDGE_DARK, inner)
            pygame.draw.ellipse(self.screen, COLOR_TOXIC_SLUDGE, inner.inflate(-4, -4))
            bubble_r = 3 + int(math.sin(self.anim_timer * 7) * 1.5)
            pygame.draw.circle(self.screen, (190, 242, 100), (cx - 3, cy - 2), bubble_r, 1)
            pygame.draw.circle(self.screen, (255, 255, 255), (cx + 4, cy + 3), 1)

        elif obs_type == 4:
            pygame.draw.rect(self.screen, COLOR_ENGINE_DARK, inner, border_radius=2)
            pygame.draw.rect(self.screen, COLOR_ENGINE_RUST, inner, 2, border_radius=2)
            pygame.draw.line(self.screen, (245, 158, 11), (inner.left + 3, inner.top + 5), (inner.right - 3, inner.bottom - 5), 2)
            pygame.draw.line(self.screen, (56, 189, 248), (inner.left + 3, inner.bottom - 5), (inner.right - 3, inner.top + 5), 1)

        elif obs_type == 5:
            pygame.draw.rect(self.screen, COLOR_MO_WHITE, (cx - 8, cy - 6, 16, 14), border_radius=4)
            pygame.draw.rect(self.screen, (148, 163, 184), (cx - 8, cy - 6, 16, 14), 1, border_radius=4)
            pygame.draw.circle(self.screen, COLOR_MO_BEACON, (cx, cy - 8), 3)
            pygame.draw.rect(self.screen, (71, 85, 105), (cx - 7, cy + 5, 14, 3))

    def _draw_walle(self, cx: int, cy: int, size: int, facing: str):
        body_w, body_h = int(size * 0.65), int(size * 0.60)
        body_rect = pygame.Rect(cx - body_w // 2, cy - body_h // 2 + 3, body_w, body_h)
        pygame.draw.rect(self.screen, COLOR_WALLE_YELLOW, body_rect, border_radius=3)
        pygame.draw.rect(self.screen, (180, 83, 9), body_rect, 1, border_radius=3)

        pygame.draw.line(self.screen, (60, 40, 20), (body_rect.left + 3, cy + 2), (body_rect.right - 3, cy + 2), 1)
        pygame.draw.rect(self.screen, (30, 41, 59), (cx - 4, cy - 2, 8, 4))

        tread_w, tread_h = 4, body_h + 4
        pygame.draw.rect(self.screen, COLOR_WALLE_TREADS, (body_rect.left - tread_w, cy - tread_h // 2 + 3, tread_w, tread_h), border_radius=2)
        pygame.draw.rect(self.screen, COLOR_WALLE_TREADS, (body_rect.right, cy - tread_h // 2 + 3, tread_w, tread_h), border_radius=2)

        eye_y = body_rect.top - 5
        eye_spacing = 5
        eye_w, eye_h = 6, 7

        look_ox = 2 if facing == "RIGHT" else (-2 if facing == "LEFT" else 0)
        look_oy = 2 if facing == "DOWN" else (-2 if facing == "UP" else 0)

        pygame.draw.rect(self.screen, (160, 160, 170), (cx - eye_spacing - eye_w + look_ox, eye_y + look_oy, eye_w, eye_h), border_radius=2)
        pygame.draw.rect(self.screen, (160, 160, 170), (cx + eye_spacing - 2 + look_ox, eye_y + look_oy, eye_w, eye_h), border_radius=2)

        pygame.draw.circle(self.screen, COLOR_WALLE_EYE_GLASS, (cx - eye_spacing - eye_w // 2 + look_ox, eye_y + eye_h // 2 + look_oy), 2)
        pygame.draw.circle(self.screen, COLOR_WALLE_EYE_GLASS, (cx + eye_spacing + eye_w // 2 - 2 + look_ox, eye_y + eye_h // 2 + look_oy), 2)

    def _draw_plant_in_boot(self, cx: int, cy: int):
        boot_points = [
            (cx - 6, cy + 8),
            (cx + 8, cy + 8),
            (cx + 8, cy + 3),
            (cx + 2, cy + 1),
            (cx + 2, cy - 4),
            (cx - 6, cy - 4),
        ]
        pygame.draw.polygon(self.screen, COLOR_BOOT_BROWN, boot_points)
        pygame.draw.polygon(self.screen, (67, 28, 10), boot_points, 1)

        stem_start = (cx - 2, cy - 4)
        stem_end = (cx - 1, cy - 11)
        pygame.draw.line(self.screen, COLOR_PLANT_GREEN, stem_start, stem_end, 2)

        pulse = math.sin(self.anim_timer * 6) * 1.5
        pygame.draw.ellipse(self.screen, COLOR_PLANT_GREEN, (cx - 7, cy - 14, 6 + int(pulse), 4))
        pygame.draw.ellipse(self.screen, (74, 222, 128), (cx - 1, cy - 16, 7 + int(pulse), 4))
        pygame.draw.circle(self.screen, (*COLOR_PLANT_GREEN, 100), (cx, cy - 12), 4, 1)

    # -------------------------------------------------------------------------
    # RENDERING METHODS
    # -------------------------------------------------------------------------
    def draw_grid_environment(self):
        grid_rect = pygame.Rect(GRID_OFFSET_X, GRID_OFFSET_Y, GRID_PIXELS, GRID_PIXELS)
        pygame.draw.rect(self.screen, COLOR_GRID_BG, grid_rect)

        current_pos = getattr(self.agent, "current_position", self.start_pos)
        facing = getattr(self.agent, "facing", "RIGHT")

        # 1. Grid Cells (5 Obstacle Types & Scrap Dots)
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                px = GRID_OFFSET_X + x * CELL_SIZE
                py = GRID_OFFSET_Y + y * CELL_SIZE
                cell_rect = pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)
                cell_val = self.grid[y][x]

                if cell_val != 0:
                    self._draw_obstacle(cell_rect, cell_val)
                else:
                    pygame.draw.rect(self.screen, (35, 30, 26), cell_rect, 1)
                    if (x + y) % 3 == 0 and (x, y) not in self.cleared_scrap:
                        pygame.draw.circle(self.screen, (70, 60, 50), cell_rect.center, 2)

        # 2. Step-by-Step Search Probing Lines (Cyan on Safe probe, RED on Collision!)
        for (f_pos, t_pos, is_safe) in self.active_probe_segments:
            fx = GRID_OFFSET_X + f_pos[0] * CELL_SIZE + CELL_SIZE // 2
            fy = GRID_OFFSET_Y + f_pos[1] * CELL_SIZE + CELL_SIZE // 2
            tx = GRID_OFFSET_X + t_pos[0] * CELL_SIZE + CELL_SIZE // 2
            ty = GRID_OFFSET_Y + t_pos[1] * CELL_SIZE + CELL_SIZE // 2

            line_col = COLOR_PROBE_SAFE if is_safe else COLOR_PROBE_COLLISION
            pygame.draw.line(self.screen, line_col, (fx, fy), (tx, ty), 3 if is_safe else 4)

            if not is_safe:
                pygame.draw.circle(self.screen, COLOR_PROBE_COLLISION, (tx, ty), 5)

        # 3. Traversed Trail & Planned Remaining Route
        # A. Traversed Footprint Trail behind WALL•E (Subtle Cyan Line)
        if len(self.visited_trail) >= 2:
            visited_pts = [
                (
                    GRID_OFFSET_X + p[0] * CELL_SIZE + CELL_SIZE // 2,
                    GRID_OFFSET_Y + p[1] * CELL_SIZE + CELL_SIZE // 2,
                )
                for p in self.visited_trail
            ]
            pygame.draw.lines(self.screen, COLOR_TRAIL_VISITED, False, visited_pts, 3)
            for pt in visited_pts[:-1]:
                pygame.draw.circle(self.screen, (56, 189, 248), pt, 3)

        # B. ONLY ONE Single True Yellow Route Ahead (Strictly contiguous from current position to Plant!)
        remaining_path = self.agent.get_path() if hasattr(self.agent, "get_path") else []
        if len(remaining_path) > 0 and not self.is_probing_path:
            ahead_route = [current_pos] + list(remaining_path)
            ahead_pts = [
                (
                    GRID_OFFSET_X + p[0] * CELL_SIZE + CELL_SIZE // 2,
                    GRID_OFFSET_Y + p[1] * CELL_SIZE + CELL_SIZE // 2,
                )
                for p in ahead_route
            ]
            if len(ahead_pts) >= 2:
                pygame.draw.lines(self.screen, COLOR_PATH_TRAIL, False, ahead_pts, 4)
            for pt in ahead_pts[1:]:
                pygame.draw.circle(self.screen, COLOR_TEXT_PRIMARY, pt, 4)

        # 4. Target Goal (Plant in the Boot)
        gx, gy = self.goal_pos
        gcx = GRID_OFFSET_X + gx * CELL_SIZE + CELL_SIZE // 2
        gcy = GRID_OFFSET_Y + gy * CELL_SIZE + CELL_SIZE // 2
        self._draw_plant_in_boot(gcx, gcy)

        # 5. WALL•E Agent
        ax, ay = current_pos
        acx = GRID_OFFSET_X + ax * CELL_SIZE + CELL_SIZE // 2
        acy = GRID_OFFSET_Y + ay * CELL_SIZE + CELL_SIZE // 2
        self._draw_walle(acx, acy, CELL_SIZE - 4, facing)

        # Grid Border
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, grid_rect, 3, border_radius=6)

    def draw_telemetry_dashboard(self):
        panel_rect = pygame.Rect(PANEL_X, GRID_OFFSET_Y, PANEL_WIDTH, GRID_PIXELS)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, panel_rect, 3, border_radius=8)

        cur_y = GRID_OFFSET_Y + 16
        pad_x = PANEL_X + 20
        content_w = PANEL_WIDTH - 40

        title_surf = self.font_title.render("WALL•E // BnL DIRECTIVE", True, COLOR_TEXT_AMBER)
        self.screen.blit(title_surf, (pad_x, cur_y))
        cur_y += 28

        sub_surf = self.font_sub.render("STEP-BY-STEP PROBE & BACKTRACK", True, COLOR_TEXT_CYAN)
        self.screen.blit(sub_surf, (pad_x, cur_y))
        cur_y += 20

        pygame.draw.line(self.screen, (87, 83, 78), (pad_x, cur_y), (pad_x + content_w, cur_y), 2)
        cur_y += 12

        # --- SECTION 1: INTERACTIVE BUTTONS ---
        mouse_pos = pygame.mouse.get_pos()

        # [🔍 FIND PATH] BUTTON
        self.btn_find_path.y = cur_y
        hov_find = self.btn_find_path.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, COLOR_BUTTON_ACTION if hov_find else (18, 83, 40), self.btn_find_path, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_TEXT_GREEN, self.btn_find_path, 2, border_radius=6)

        btn_find_text = "🔍 FIND PATH (STEP-BY-STEP)" if not self.is_probing_path else "⚡ AI PROBING PATH..."
        t1 = self.font_badge.render(btn_find_text, True, COLOR_TEXT_PRIMARY)
        self.screen.blit(t1, t1.get_rect(center=self.btn_find_path.center))
        cur_y += 48

        # [🔄 REFRESH SECTOR] BUTTON
        self.btn_refresh.y = cur_y
        hov_ref = self.btn_refresh.collidepoint(mouse_pos)
        pygame.draw.rect(self.screen, COLOR_BUTTON_HOVER if hov_ref else (44, 30, 20), self.btn_refresh, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_TEXT_AMBER, self.btn_refresh, 2, border_radius=6)

        t2 = self.font_body.render(f"🔄 REFRESH SECTOR (MAP #{self.sector_index + 1})", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(t2, t2.get_rect(center=self.btn_refresh.center))
        cur_y += 46

        # --- SECTION 2: KB DIRECTIVE STATUS BADGE ---
        state_str = self.agent.get_state()
        if self.is_probing_path:
            state_str = "PROBING"
        elif not self.is_simulating and state_str not in ("REACHED_GOAL", "FAILED"):
            state_str = "PAUSED" if state_str != "IDLE" else "READY"

        state_palette = {
            "ACTING": (COLOR_TEXT_AMBER, "DIRECTIVE ACTIVE: ROLLING"),
            "PROBING": (COLOR_TEXT_CYAN, "AI PROBING & BACKTRACKING..."),
            "REPLANNING": (COLOR_TEXT_RED, "KB TRIGGER: PerceiveHazard ⇒ ¬Move"),
            "REACHED_GOAL": (COLOR_TEXT_GREEN, "PLANT SECURED! COMPLETE!"),
            "FAILED": (COLOR_TEXT_RED, "IMPASSABLE: NO PATH FOUND"),
            "PAUSED": (COLOR_TEXT_PRIMARY, "SIMULATION PAUSED"),
            "READY": (COLOR_TEXT_GREEN, "PATH LOCKED: PRESS SPACE"),
        }
        col, desc = state_palette.get(state_str, (COLOR_TEXT_PRIMARY, state_str))

        pill_rect = pygame.Rect(pad_x, cur_y, content_w, 34)
        pygame.draw.rect(self.screen, (15, 12, 10), pill_rect, border_radius=6)
        pygame.draw.rect(self.screen, col, pill_rect, 2, border_radius=6)

        pill_text = self.font_badge.render(f"● {desc}", True, col)
        self.screen.blit(pill_text, pill_text.get_rect(center=pill_rect.center))
        cur_y += 42

        # --- SECTION 3: PERFORMANCE METRICS ---
        metrics = self.agent.get_metrics()
        remaining_len = len(self.agent.get_path())
        collisions = getattr(metrics, "collisions_avoided", 0)
        inferences = getattr(metrics, "logical_inferences", 0)

        metric_cards = [
            ("REMAINING PATH", f"{remaining_len} steps", COLOR_TEXT_GREEN),
            ("COLLISIONS EVADED", f"{collisions} blocks", COLOR_TEXT_RED),
            ("KB INFERENCES", f"{inferences} proofs", COLOR_TEXT_CYAN),
            ("PROBE SEGMENTS", f"{len(self.active_probe_segments)}", COLOR_TEXT_AMBER),
        ]

        card_w = (content_w - 12) // 2
        card_h = 48

        for i, (label, val, col) in enumerate(metric_cards):
            cx = pad_x + (i % 2) * (card_w + 12)
            cy = cur_y + (i // 2) * (card_h + 8)
            card_rect = pygame.Rect(cx, cy, card_w, card_h)

            pygame.draw.rect(self.screen, (20, 16, 14), card_rect, border_radius=6)
            pygame.draw.rect(self.screen, (68, 55, 45), card_rect, 1, border_radius=6)

            lbl_surf = self.font_body.render(label, True, (168, 162, 158))
            val_surf = self.font_sub.render(val, True, col)

            self.screen.blit(lbl_surf, (cx + 6, cy + 4))
            self.screen.blit(val_surf, (cx + 6, cy + 22))

        cur_y += 2 * (card_h + 8) + 6

        # --- SECTION 4: SCROLLABLE REAL-TIME PROBING FEED ---
        feed_lbl = self.font_sub.render("LIVE PROBING & COLLISION FEED", True, COLOR_TEXT_AMBER)
        self.screen.blit(feed_lbl, (pad_x, cur_y))

        # Scroll hint indicator
        scroll_hint = self.font_mono.render("↕ SCROLLABLE", True, (148, 163, 184))
        self.screen.blit(scroll_hint, (pad_x + content_w - scroll_hint.get_width(), cur_y + 2))
        cur_y += 18

        self.feed_box_rect = pygame.Rect(pad_x, cur_y, content_w, 145)
        pygame.draw.rect(self.screen, (12, 10, 8), self.feed_box_rect, border_radius=6)
        pygame.draw.rect(self.screen, (55, 45, 35), self.feed_box_rect, 1, border_radius=6)

        # Calculate visible window
        visible_lines = 6
        total_logs = len(self.action_logs)
        max_scroll = max(0, total_logs - visible_lines)
        self.log_scroll_pos = max(0, min(max_scroll, self.log_scroll_pos))

        start_idx = max(0, total_logs - visible_lines - self.log_scroll_pos)
        end_idx = min(total_logs, start_idx + visible_lines)
        displayed_logs = self.action_logs[start_idx:end_idx]

        # Hardware clipping region so text never overflows past the feed box
        clip_rect = pygame.Rect(pad_x + 4, cur_y + 4, content_w - 20, 137)
        self.screen.set_clip(clip_rect)

        feed_y = cur_y + 6
        max_text_width = content_w - 24

        for entry in displayed_logs:
            col = COLOR_TEXT_PRIMARY
            if "COLLISION" in entry or "HAZARD" in entry:
                col = COLOR_TEXT_RED
            elif "BACKTRACK" in entry:
                col = COLOR_TEXT_AMBER
            elif "SAFE" in entry or "COMPLETE" in entry or "DISCOVERED" in entry:
                col = COLOR_TEXT_GREEN
            elif "PROBING" in entry or "SECTOR" in entry:
                col = COLOR_TEXT_CYAN

            # Truncate text if needed to strictly prevent out-of-bounds rendering
            display_text = entry
            while len(display_text) > 8 and self.font_mono.size(display_text)[0] > max_text_width:
                display_text = display_text[:-4] + "..."

            line_surf = self.font_mono.render(display_text, True, col)
            self.screen.blit(line_surf, (pad_x + 8, feed_y))
            feed_y += 22

        # Reset clipping to full screen
        self.screen.set_clip(None)

        # Draw Scrollbar Track & Thumb
        if total_logs > visible_lines:
            track_rect = pygame.Rect(self.feed_box_rect.right - 10, self.feed_box_rect.y + 6, 5, self.feed_box_rect.height - 12)
            pygame.draw.rect(self.screen, (35, 30, 25), track_rect, border_radius=2)

            thumb_h = max(18, int(track_rect.height * (visible_lines / total_logs)))
            scroll_ratio = 1.0 - (self.log_scroll_pos / max_scroll) if max_scroll > 0 else 1.0
            thumb_y = track_rect.y + int((track_rect.height - thumb_h) * scroll_ratio)
            thumb_rect = pygame.Rect(track_rect.x, thumb_y, track_rect.width, thumb_h)
            pygame.draw.rect(self.screen, COLOR_TEXT_AMBER, thumb_rect, border_radius=2)

        cur_y += 152

        # --- SECTION 5: OPERATOR CONTROLS ---
        ctrl_box = pygame.Rect(pad_x, cur_y, content_w, 95)
        pygame.draw.rect(self.screen, (20, 16, 14), ctrl_box, border_radius=6)
        pygame.draw.rect(self.screen, (68, 55, 45), ctrl_box, 1, border_radius=6)

        ctrl_title = self.font_sub.render("OPERATOR SHORTCUTS", True, COLOR_TEXT_AMBER)
        self.screen.blit(ctrl_title, (pad_x + 8, cur_y + 5))

        controls = [
            ("[F]", "Trigger Step-by-Step Find Path"),
            ("[SPACE]", "Execute Roll to Plant"),
            ("[CLICK]", "Cycle 5 Obstacle Types on Grid"),
            ("[SCROLL]", "Scroll Live Probing Log History"),
        ]
        for idx, (key, desc) in enumerate(controls):
            k_surf = self.font_mono.render(key, True, COLOR_TEXT_CYAN)
            d_surf = self.font_body.render(desc, True, COLOR_TEXT_PRIMARY)
            row_y = cur_y + 24 + idx * 17
            self.screen.blit(k_surf, (pad_x + 8, row_y))
            self.screen.blit(d_surf, (pad_x + 80, row_y))

    def draw_route_found_modal(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        m_w, m_h = 540, 310
        m_x = (WINDOW_WIDTH - m_w) // 2
        m_y = (WINDOW_HEIGHT - m_h) // 2
        modal_rect = pygame.Rect(m_x, m_y, m_w, m_h)

        pygame.draw.rect(self.screen, (24, 20, 18), modal_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_TEXT_CYAN, modal_rect, 3, border_radius=12)

        h_rect = pygame.Rect(m_x, m_y, m_w, 54)
        pygame.draw.rect(self.screen, (14, 116, 144), h_rect, border_top_left_radius=12, border_top_right_radius=12)
        t_surf = self.font_modal_title.render("🚀 DIRECTIVE ROUTE DISCOVERED!", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(t_surf, t_surf.get_rect(center=h_rect.center))

        msg1 = self.font_sub.render("WALL•E HAS MAPPED A SAFE PASSAGE TO THE PLANT!", True, COLOR_TEXT_GREEN)
        msg2 = self.font_body.render("Propositional KB avoided all Secur-T drones and toxic hazards.", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(msg1, msg1.get_rect(center=(m_x + m_w // 2, m_y + 82)))
        self.screen.blit(msg2, msg2.get_rect(center=(m_x + m_w // 2, m_y + 110)))

        info_rect = pygame.Rect(m_x + 30, m_y + 135, m_w - 60, 65)
        pygame.draw.rect(self.screen, (15, 12, 10), info_rect, border_radius=6)
        pygame.draw.rect(self.screen, (68, 55, 45), info_rect, 1, border_radius=6)

        path_len = len(self.agent.get_path())
        s1 = self.font_mono.render(f"VERIFIED ROUTE: {path_len} BLOCKS  |  COLLISIONS EVADED: {self.agent.metrics.collisions_avoided}", True, COLOR_TEXT_AMBER)
        s2 = self.font_mono.render(f"KB SENTENCES: {self.agent.metrics.kb_clauses_count}  |  STATUS: PROVEN SAFE", True, COLOR_TEXT_CYAN)
        self.screen.blit(s1, (info_rect.x + 14, info_rect.y + 12))
        self.screen.blit(s2, (info_rect.x + 14, info_rect.y + 36))

        mouse_pos = pygame.mouse.get_pos()
        self.modal_btn_action = pygame.Rect(m_x + 35, m_y + 230, 250, 44)
        self.modal_btn_dismiss = pygame.Rect(m_x + m_w - 200, m_y + 230, 165, 44)

        hov_act = self.modal_btn_action.collidepoint(mouse_pos)
        hov_dis = self.modal_btn_dismiss.collidepoint(mouse_pos)

        pygame.draw.rect(self.screen, (22, 101, 52) if hov_act else (20, 83, 45), self.modal_btn_action, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_TEXT_GREEN, self.modal_btn_action, 2, border_radius=6)
        b1 = self.font_sub.render("▶ EXECUTE DIRECTIVE (ROLL)", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(b1, b1.get_rect(center=self.modal_btn_action.center))

        pygame.draw.rect(self.screen, (68, 40, 15) if hov_dis else (44, 30, 20), self.modal_btn_dismiss, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_TEXT_AMBER, self.modal_btn_dismiss, 2, border_radius=6)
        b2 = self.font_sub.render("DISMISS [SPACE]", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(b2, b2.get_rect(center=self.modal_btn_dismiss.center))

    def draw_mission_complete_modal(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        m_w, m_h = 520, 310
        m_x = (WINDOW_WIDTH - m_w) // 2
        m_y = (WINDOW_HEIGHT - m_h) // 2
        modal_rect = pygame.Rect(m_x, m_y, m_w, m_h)

        pygame.draw.rect(self.screen, (24, 20, 18), modal_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_TEXT_GREEN, modal_rect, 3, border_radius=12)

        header_rect = pygame.Rect(m_x, m_y, m_w, 54)
        pygame.draw.rect(self.screen, (22, 101, 52), header_rect, border_top_left_radius=12, border_top_right_radius=12)
        title_surf = self.font_modal_title.render("🌱 DIRECTIVE COMPLETE!", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(title_surf, title_surf.get_rect(center=header_rect.center))

        msg1 = self.font_sub.render("WALL•E REACHED THE PLANT LOCATION!", True, COLOR_TEXT_PRIMARY)
        msg2 = self.font_body.render("Earth seedling secured. Axiom recolonization authorized.", True, COLOR_TEXT_CYAN)
        self.screen.blit(msg1, msg1.get_rect(center=(m_x + m_w // 2, m_y + 85)))
        self.screen.blit(msg2, msg2.get_rect(center=(m_x + m_w // 2, m_y + 115)))

        mouse_pos = pygame.mouse.get_pos()
        self.modal_btn_action = pygame.Rect(m_x + 35, m_y + 230, 220, 44)
        self.modal_btn_dismiss = pygame.Rect(m_x + m_w - 220, m_y + 230, 185, 44)

        hov_act = self.modal_btn_action.collidepoint(mouse_pos)
        hov_dis = self.modal_btn_dismiss.collidepoint(mouse_pos)

        pygame.draw.rect(self.screen, (22, 101, 52) if hov_act else (20, 83, 45), self.modal_btn_action, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_TEXT_GREEN, self.modal_btn_action, 2, border_radius=6)
        b1 = self.font_sub.render("🔄 NEXT SECTOR [N]", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(b1, b1.get_rect(center=self.modal_btn_action.center))

        pygame.draw.rect(self.screen, (68, 40, 15) if hov_dis else (44, 30, 20), self.modal_btn_dismiss, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_TEXT_AMBER, self.modal_btn_dismiss, 2, border_radius=6)
        b2 = self.font_sub.render("↺ BASE CAMP [R]", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(b2, b2.get_rect(center=self.modal_btn_dismiss.center))

    # -------------------------------------------------------------------------
    # MAIN SIMULATION & SEARCH LOOP
    # -------------------------------------------------------------------------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            self.anim_timer += dt

            # 1. Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEWHEEL:
                    if self.feed_box_rect.collidepoint(pygame.mouse.get_pos()):
                        max_scroll = max(0, len(self.action_logs) - 6)
                        self.log_scroll_pos = max(0, min(max_scroll, self.log_scroll_pos + event.y * 2))
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_f:
                        self.start_stepped_path_find()
                    elif event.key == pygame.K_SPACE:
                        if self.show_route_found_modal:
                            self.show_route_found_modal = False
                            self.is_simulating = True
                        elif self.show_mission_complete_modal:
                            self.show_mission_complete_modal = False
                        else:
                            self.is_simulating = not self.is_simulating
                            state_tag = "RESUMED" if self.is_simulating else "PAUSED"
                            self.log(f"DIRECTIVE {state_tag}")
                    elif event.key == pygame.K_PAGEUP or event.key == pygame.K_UP:
                        max_scroll = max(0, len(self.action_logs) - 6)
                        self.log_scroll_pos = min(max_scroll, self.log_scroll_pos + 2)
                    elif event.key == pygame.K_PAGEDOWN or event.key == pygame.K_DOWN:
                        self.log_scroll_pos = max(0, self.log_scroll_pos - 2)
                    elif event.key == pygame.K_n:
                        self.refresh_sector()
                    elif event.key == pygame.K_r:
                        self.reset_simulation()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_click(event.pos)

            # 2. Stepped Search Probe Execution
            if self.is_probing_path:
                if self.trace_idx < len(self.search_trace):
                    event_type, f_pos, t_pos, is_safe, log_msg = self.search_trace[self.trace_idx]

                    if event_type == "probe":
                        self.active_probe_segments.append((f_pos, t_pos, is_safe))
                        self.log(log_msg)
                    elif event_type == "backtrack":
                        if self.active_probe_segments and not self.active_probe_segments[-1][2]:
                            self.active_probe_segments.pop()
                        self.log(log_msg)

                    self.trace_idx += 1
                else:
                    self.is_probing_path = False
                    self.show_route_found_modal = True
                    self.log(f"DIRECTIVE ROUTE LOCKED: {len(self.agent.get_path())} BLOCKS TO SEEDLING.")

            # 3. WALL•E Movement Step Execution (Along found path)
            current_time = time.time()
            if self.is_simulating and not self.is_probing_path and not self.show_route_found_modal and (current_time - self.last_step_time >= self.step_delay):
                self.last_step_time = current_time
                if hasattr(self.agent, "step"):
                    self.agent.step(self.grid)
                    curr_p = getattr(self.agent, "current_position", self.start_pos)
                    self.cleared_scrap.add(curr_p)

                    # Continuous visited footprint trail
                    if not self.visited_trail or self.visited_trail[-1] != curr_p:
                        self.visited_trail.append(curr_p)

                    if hasattr(self.agent, "last_action_msg"):
                        self.log(self.agent.last_action_msg)

                    state = (
                        self.agent.get_state()
                        if hasattr(self.agent, "get_state")
                        else getattr(self.agent, "state", "")
                    )
                    if state == "REACHED_GOAL":
                        self.is_simulating = False
                        self.show_mission_complete_modal = True
                    elif state == "FAILED":
                        self.is_simulating = False

            # 4. Drawing
            self.screen.fill(COLOR_BG)
            self.draw_grid_environment()
            self.draw_telemetry_dashboard()

            if self.show_route_found_modal:
                self.draw_route_found_modal()
            elif self.show_mission_complete_modal:
                self.draw_mission_complete_modal()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# -----------------------------------------------------------------------------
# 6. ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app = AuraWalleStepGUI()
    app.run()

