"""
================================================================================
AURA: Autonomous Understanding & Replanning Agent
PIXAR WALL-E RECLAMATION DIRECTIVE

PART 1 of 3: KNOWLEDGE BASE & AGENT LOGIC
--------------------------------------------------------------------------------
This is one of three files that together make up the original aihackathon1.py
program, split for readability. No functionality was changed or removed -
running part3_gui.py (which imports the other two) reproduces the exact same
application as the original single file.

  Part 1 (this file)  -> aihackathon1_part1_logic.py  : Propositional Logic KB
                                                          + Knowledge-Based Agent
  Part 2               -> aihackathon1_part2_world.py  : Colors/dimensions
                                                          + Scrap world generator
  Part 3               -> aihackathon1_part3_gui.py    : Pygame GUI + entry point

Run the program with:  python aihackathon1_part3_gui.py
================================================================================
"""

from dataclasses import dataclass
from typing import List, Tuple, Set, Dict, Optional, FrozenSet

# -----------------------------------------------------------------------------
# 1. PROPOSITIONAL LOGIC KNOWLEDGE BASE & RESOLUTION ENGINE
# -----------------------------------------------------------------------------
Literal = Tuple[str, Tuple[int, int], bool]
Clause = FrozenSet[Literal]


class PropositionalKB:
    """Propositional Logic Knowledge Base with Resolution Refutation."""
    def __init__(self):
        self.clauses: Set[Clause] = set()

    def tell_fact(self, predicate: str, pos: Tuple[int, int], positive: bool = True):
        lit: Literal = (predicate, pos, positive)
        self.clauses.add(frozenset([lit]))

    def tell_rule_implication(self, p_pred: str, q_pred: str, pos: Tuple[int, int], q_positive: bool = False):
        p_lit: Literal = (p_pred, pos, False)
        q_lit: Literal = (q_pred, pos, q_positive)
        self.clauses.add(frozenset([p_lit, q_lit]))

    def _resolve(self, c1: Clause, c2: Clause) -> Set[Clause]:
        resolvents = set()
        for lit1 in c1:
            comp_lit = (lit1[0], lit1[1], not lit1[2])
            if comp_lit in c2:
                res = (set(c1) | set(c2)) - {lit1, comp_lit}
                resolvents.add(frozenset(res))
        return resolvents

    def ask_resolution(self, query_pred: str, pos: Tuple[int, int], query_positive: bool = True) -> bool:
        negated_query_lit: Literal = (query_pred, pos, not query_positive)
        clauses = set(self.clauses)
        clauses.add(frozenset([negated_query_lit]))
        new_clauses = set()

        steps = 0
        while steps < 80:
            steps += 1
            clause_list = list(clauses)
            n = len(clause_list)

            for i in range(n):
                for j in range(i + 1, n):
                    resolvents = self._resolve(clause_list[i], clause_list[j])
                    for res in resolvents:
                        if len(res) == 0:
                            return True
                        new_clauses.add(res)

            if new_clauses.issubset(clauses):
                break
            clauses.update(new_clauses)
        return False


# -----------------------------------------------------------------------------
# 2. KNOWLEDGE-BASED LOGICAL AGENT WITH SEARCH PROBE TRACING
# -----------------------------------------------------------------------------
@dataclass
class Metrics:
    path_cost: int = 0
    nodes_expanded: int = 0
    replan_count: int = 0
    time_taken_ms: float = 0.0
    kb_clauses_count: int = 0
    logical_inferences: int = 0
    collisions_avoided: int = 0


TraceEvent = Tuple[str, Tuple[int, int], Tuple[int, int], bool, str]


class KnowledgeBasedAgent:
    def __init__(self, start_pos: Tuple[int, int] = (1, 1), goal_pos: Tuple[int, int] = (18, 18)):
        self.start_pos = start_pos
        self.goal_pos = goal_pos
        self.current_position = start_pos
        self.state = "IDLE"
        self.path: List[Tuple[int, int]] = []
        self.explored_nodes: Set[Tuple[int, int]] = set()
        self.metrics = Metrics()
        self.facing = "RIGHT"
        self.last_action_msg = "WALL•E KB online. Ready for Directive."

        self.kb = PropositionalKB()
        self.proven_safe: Set[Tuple[int, int]] = {start_pos}
        self.entailed_hazards: Set[Tuple[int, int]] = set()
        self.kb.tell_fact("Safe", self.start_pos, True)

    def get_state(self) -> str:
        return self.state

    def get_metrics(self) -> Metrics:
        self.metrics.kb_clauses_count = len(self.kb.clauses)
        return self.metrics

    def get_path(self) -> List[Tuple[int, int]]:
        return self.path

    def get_explored_nodes(self) -> Set[Tuple[int, int]]:
        return self.explored_nodes

    def perceive_and_tell(self, grid: List[List[int]], current_pos: Tuple[int, int]):
        rows, cols = len(grid), len(grid[0])
        x, y = current_pos

        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cols and 0 <= ny < rows:
                cell_val = grid[ny][nx]
                pos = (nx, ny)
                self.kb.tell_rule_implication("HazardSignal", "Safe", pos, q_positive=False)

                if cell_val != 0:
                    self.kb.tell_fact("HazardSignal", pos, True)
                    if self.kb.ask_resolution("HazardSignal", pos, True):
                        self.entailed_hazards.add(pos)
                        self.metrics.logical_inferences += 1
                else:
                    self.kb.tell_fact("Safe", pos, True)
                    self.proven_safe.add(pos)
                    self.metrics.logical_inferences += 1

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def generate_search_trace(self, grid: List[List[int]]) -> Tuple[List[TraceEvent], List[Tuple[int, int]]]:
        """
        Simulates step-by-step search exploration with live probes, red collisions,
        and backtracking branch returns for visualization.
        """
        rows, cols = len(grid), len(grid[0])
        start = self.current_position
        goal = self.goal_pos
        trace: List[TraceEvent] = []

        self.perceive_and_tell(grid, start)

        open_set = {start}
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, goal)}

        visited = set()
        nodes_expanded = 0
        obstacle_names = {
            1: "Scrap Metal Cube",
            2: "Axiom Secur-T Drone",
            3: "Radioactive Sludge Pool",
            4: "Crushed Engine Frame",
            5: "M-O Cleaner Bot"
        }

        while open_set:
            current = min(open_set, key=lambda pos: f_score.get(pos, float('inf')))
            open_set.remove(current)
            visited.add(current)
            nodes_expanded += 1

            if current == goal:
                path = []
                curr = current
                while curr in came_from:
                    path.append(curr)
                    curr = came_from[curr]
                path.reverse()
                self.path = path
                self.metrics.path_cost = len(path)
                self.metrics.nodes_expanded += nodes_expanded
                return trace, path

            cx, cy = current
            dir_names = {(0, -1): "UP", (1, 0): "RIGHT", (0, 1): "DOWN", (-1, 0): "LEFT"}

            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                nx, ny = cx + dx, cy + dy
                d_name = dir_names.get((dx, dy), "FORWARD")

                if 0 <= nx < cols and 0 <= ny < rows:
                    neighbor = (nx, ny)
                    cell_val = grid[ny][nx]

                    if cell_val != 0 or neighbor in self.entailed_hazards:
                        obs_name = obstacle_names.get(cell_val, "Hazard")
                        msg = f"COLLISION @ ({nx},{ny})! Hit {obs_name}. Rule: PerceiveHazard ⇒ ¬Move!"
                        trace.append(("probe", current, neighbor, False, msg))
                        self.metrics.collisions_avoided += 1
                        trace.append(("backtrack", neighbor, current, False, f"Backtracking from ({nx},{ny}) to ({cx},{cy})."))
                        continue

                    if neighbor in visited:
                        continue

                    tentative_g = g_score[current] + 1
                    if tentative_g < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score[neighbor] = tentative_g + self._heuristic(neighbor, goal)
                        open_set.add(neighbor)

                        msg = f"PROBING {d_name} -> Sector ({nx},{ny}) SAFE. Extending route."
                        trace.append(("probe", current, neighbor, True, msg))

        return trace, []

    def plan(self, grid: List[List[int]]) -> bool:
        trace, path = self.generate_search_trace(grid)
        return len(path) > 0

    def step(self, grid: List[List[int]]) -> dict:
        if self.current_position == self.goal_pos:
            self.state = "REACHED_GOAL"
            self.last_action_msg = "PLANT SECURED! Directive Complete!"
            return {"action": "GOAL", "position": self.current_position, "state": self.state}

        self.perceive_and_tell(grid, self.current_position)

        path_blocked = False
        if self.path:
            next_step = self.path[0]
            if grid[next_step[1]][next_step[0]] != 0 or next_step in self.entailed_hazards:
                path_blocked = True

        if not self.path or path_blocked:
            self.state = "REPLANNING"
            self.metrics.replan_count += 1
            self.last_action_msg = f"KB TRIGGER: PerceiveHazard ⇒ ¬Move! Replanning (#{self.metrics.replan_count})..."
            success = self.plan(grid)
            if not success:
                self.state = "FAILED"
                return {"action": "FAILED", "position": self.current_position, "state": self.state}

        if self.path:
            next_pos = self.path.pop(0)
            dx = next_pos[0] - self.current_position[0]
            dy = next_pos[1] - self.current_position[1]
            
            if dx == 1: self.facing = "RIGHT"
            elif dx == -1: self.facing = "LEFT"
            elif dy == 1: self.facing = "DOWN"
            elif dy == -1: self.facing = "UP"

            self.current_position = next_pos
            self.proven_safe.add(next_pos)
            self.state = "ACTING"
            self.metrics.path_cost = len(self.path)
            self.last_action_msg = f"WALL•E rolled {self.facing} to ({next_pos[0]}, {next_pos[1]})"

            if self.current_position == self.goal_pos:
                self.state = "REACHED_GOAL"
                self.last_action_msg = "DIRECTIVE COMPLETE: Living seedling secured!"

            return {"action": self.facing, "position": self.current_position, "state": self.state}

        self.state = "FAILED"
        self.last_action_msg = "Logical inference: No safe moves available."
        return {"action": "STUCK", "position": self.current_position, "state": self.state}

    def reset(self, grid: List[List[int]]):
        self.current_position = self.start_pos
        self.state = "PLANNING"
        self.path.clear()
        self.explored_nodes.clear()
        self.metrics = Metrics()
        self.facing = "RIGHT"
        self.kb = PropositionalKB()
        self.proven_safe = {self.start_pos}
        self.entailed_hazards.clear()
        self.kb.tell_fact("Safe", self.start_pos, True)
        self.last_action_msg = "KB synchronized. Base camp ready."
        self.plan(grid)
        self.state = "IDLE"


Agent = KnowledgeBasedAgent
