"""Helpers for serving INASRA-style sparse iPuz files through the HTML5 solver.

The adapter's main job is to normalize sparse or lightly-specified INASRA exports
into a more explicit iPuz shape that the browser solver can consume reliably.
In particular, it can:

- derive across/down word locations from sparse grids,
- attach explicit cell coordinates to clue entries,
- populate the optional iPuz ``words`` section, and
- fall back to ``fakeclues`` when clue counts do not perfectly line up with the
  discovered grid entries.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BLOCK_VALUES = {"#", ".", "-"}
DEFAULT_EMPTY = "0"


@dataclass(frozen=True)
class GridEntry:
    direction: str
    number: int
    cells: list[list[int]]


def read_ipuz(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_ipuz(path: str | Path, puzzle: dict[str, Any]) -> None:
    Path(path).write_text(
        json.dumps(puzzle, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def generate_share_token(nbytes: int = 16) -> str:
    return secrets.token_urlsafe(nbytes).rstrip("=")


def normalize_inasra_ipuz(puzzle: dict[str, Any]) -> dict[str, Any]:
    """Return a solver-friendly copy of an INASRA-style sparse iPuz object."""
    normalized = json.loads(json.dumps(puzzle))
    metadata = normalized.setdefault("metadata", {})

    width = int(normalized.get("dimensions", {}).get("width") or 0)
    height = int(normalized.get("dimensions", {}).get("height") or 0)
    if width <= 0 or height <= 0:
        raise ValueError("Puzzle dimensions are missing or invalid")

    puzzle_rows = normalized.get("puzzle") or []
    solution_rows = normalized.get("solution") or []
    if not puzzle_rows or not solution_rows:
        raise ValueError("Puzzle must include both puzzle and solution grids")

    entries = derive_entries(puzzle_rows, solution_rows, width=width, height=height)
    clues = normalized.setdefault("clues", {})
    across_entries = [entry for entry in entries if entry.direction == "Across"]
    down_entries = [entry for entry in entries if entry.direction == "Down"]

    clue_counts_mismatch = False
    words_payload: list[list[dict[str, Any]]] = []

    for direction, discovered in (("Across", across_entries), ("Down", down_entries)):
        clue_list = list(clues.get(direction, []))
        attached_clues, matched = attach_cells_to_clues(clue_list, discovered)
        clues[direction] = attached_clues
        words_payload.append([{"cells": entry.cells} for entry in discovered])
        if not matched:
            clue_counts_mismatch = True

    normalized["words"] = words_payload

    # Preserve normal clue behavior when possible; otherwise drop into the solver's
    # built-in fake-clue mode so sparse / imperfectly-mapped INASRA exports still load.
    if clue_counts_mismatch:
        normalized["fakeclues"] = True
    elif "fakeclues" not in normalized:
        normalized["fakeclues"] = False

    normalized.setdefault("intro", "Exported from INASRA.")
    normalized.setdefault("origin", "INASRA")
    normalized.setdefault("publisher", "INASRA")
    normalized.setdefault("author", normalized.get("author") or "INASRA")
    normalized.setdefault("copyright", normalized.get("copyright") or "INASRA")
    metadata["inasra_sparse"] = is_sparse_layout(puzzle_rows, solution_rows)
    metadata["entry_count"] = len(entries)
    metadata["clue_counts_mismatch"] = clue_counts_mismatch
    return normalized


def attach_cells_to_clues(clues: list[Any], entries: list[GridEntry]) -> tuple[list[Any], bool]:
    """Attach explicit cells to clue objects when clue counts line up.

    Returns the updated clue list and a boolean indicating whether clue count matched
    the discovered entries.
    """
    if len(clues) != len(entries):
        return clues, False

    updated: list[Any] = []
    for clue, entry in zip(clues, entries, strict=True):
        clue_obj: dict[str, Any]
        if isinstance(clue, dict):
            clue_obj = dict(clue)
        elif isinstance(clue, list):
            number = clue[0] if clue else entry.number
            text = clue[1] if len(clue) > 1 else ""
            clue_obj = {"number": number, "clue": text}
        elif isinstance(clue, str):
            clue_obj = {"number": entry.number, "clue": clue}
        else:
            clue_obj = {"number": entry.number, "clue": str(clue)}

        clue_obj.setdefault("number", entry.number)
        clue_obj["cells"] = entry.cells
        updated.append(clue_obj)
    return updated, True


def derive_entries(
    puzzle_rows: list[list[Any]],
    solution_rows: list[list[Any]],
    *,
    width: int,
    height: int,
) -> list[GridEntry]:
    numbering_grid = compute_numbering_grid(
        puzzle_rows,
        solution_rows,
        width=width,
        height=height,
    )
    entries: list[GridEntry] = []

    for y in range(height):
        for x in range(width):
            if is_block_or_void(puzzle_rows, solution_rows, x, y):
                continue

            number = numbering_grid[y][x]
            if number is None:
                continue

            if starts_across(puzzle_rows, solution_rows, x, y, width):
                cells = collect_run(
                    puzzle_rows,
                    solution_rows,
                    x,
                    y,
                    width=width,
                    height=height,
                    dx=1,
                    dy=0,
                )
                if len(cells) > 1:
                    entries.append(GridEntry("Across", number, cells))

            if starts_down(puzzle_rows, solution_rows, x, y, height):
                cells = collect_run(
                    puzzle_rows,
                    solution_rows,
                    x,
                    y,
                    width=width,
                    height=height,
                    dx=0,
                    dy=1,
                )
                if len(cells) > 1:
                    entries.append(GridEntry("Down", number, cells))

    return entries


def compute_numbering_grid(
    puzzle_rows: list[list[Any]],
    solution_rows: list[list[Any]],
    *,
    width: int,
    height: int,
) -> list[list[int | None]]:
    numbering: list[list[int | None]] = [[None for _ in range(width)] for _ in range(height)]
    next_number = 1
    for y in range(height):
        for x in range(width):
            if is_block_or_void(puzzle_rows, solution_rows, x, y):
                continue
            if starts_across(puzzle_rows, solution_rows, x, y, width) or starts_down(
                puzzle_rows,
                solution_rows,
                x,
                y,
                height,
            ):
                numbering[y][x] = next_number
                next_number += 1
    return numbering


def starts_across(
    puzzle_rows: list[list[Any]],
    solution_rows: list[list[Any]],
    x: int,
    y: int,
    width: int,
) -> bool:
    if is_block_or_void(puzzle_rows, solution_rows, x, y):
        return False
    if x + 1 >= width or is_block_or_void(puzzle_rows, solution_rows, x + 1, y):
        return False
    return x == 0 or is_block_or_void(puzzle_rows, solution_rows, x - 1, y)


def starts_down(
    puzzle_rows: list[list[Any]],
    solution_rows: list[list[Any]],
    x: int,
    y: int,
    height: int,
) -> bool:
    if is_block_or_void(puzzle_rows, solution_rows, x, y):
        return False
    if y + 1 >= height or is_block_or_void(puzzle_rows, solution_rows, x, y + 1):
        return False
    return y == 0 or is_block_or_void(puzzle_rows, solution_rows, x, y - 1)


def collect_run(
    puzzle_rows: list[list[Any]],
    solution_rows: list[list[Any]],
    x: int,
    y: int,
    *,
    width: int,
    height: int,
    dx: int,
    dy: int,
) -> list[list[int]]:
    cells: list[list[int]] = []
    cx, cy = x, y
    while 0 <= cx < width and 0 <= cy < height and not is_block_or_void(
        puzzle_rows,
        solution_rows,
        cx,
        cy,
    ):
        cells.append([cx + 1, cy + 1])
        cx += dx
        cy += dy
    return cells


def is_sparse_layout(puzzle_rows: list[list[Any]], solution_rows: list[list[Any]]) -> bool:
    fillable = 0
    solids = 0
    for y, row in enumerate(solution_rows):
        for x, _ in enumerate(row):
            if is_block_or_void(puzzle_rows, solution_rows, x, y):
                continue
            fillable += 1
            if is_prefilled_display_value(get_cell_value(puzzle_rows, x, y)):
                solids += 1
    return fillable > 0 and solids / fillable < 0.35


def is_prefilled_display_value(value: Any) -> bool:
    if isinstance(value, dict):
        value = value.get("cell")
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text not in BLOCK_VALUES and text != DEFAULT_EMPTY


def is_block_or_void(
    puzzle_rows: list[list[Any]],
    solution_rows: list[list[Any]],
    x: int,
    y: int,
) -> bool:
    puzzle_value = get_cell_value(puzzle_rows, x, y)
    solution_value = get_cell_value(solution_rows, x, y)

    if puzzle_value is None and solution_value is None:
        return True
    if normalize_solution_text(solution_value) in BLOCK_VALUES:
        return True
    if normalize_solution_text(solution_value) == "":
        return True
    if normalize_puzzle_text(puzzle_value) in BLOCK_VALUES:
        return True
    return False


def get_cell_value(rows: list[list[Any]], x: int, y: int) -> Any:
    try:
        return rows[y][x]
    except IndexError:
        return None


def normalize_puzzle_text(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("cell")
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text == DEFAULT_EMPTY else text


def normalize_solution_text(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("value") or value.get("cell")
    if value is None:
        return ""
    return str(value).strip().upper()
