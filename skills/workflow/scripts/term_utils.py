#!/usr/bin/env python3
"""
Workflow Orchestrator — Shared Terminal Utilities

Unified ANSI escape codes, color support detection, spinner frames,
and cursor control. Used by dag.py, monitor.py, reporter.py.

Previously each script had its own copy of these (Colors / Term / C).
This module is the single source of truth.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Optional

# ── ANSI Escape Sequences ────────────────────────────────────────────────────

class Term:
    """Unified terminal control — colors, cursor, spinner, detection."""

    # ── Text Attributes ──
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # ── Foreground Colors ──
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # ── Background Colors ──
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"

    # ── Cursor & Screen Control ──
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"
    CLEAR_SCREEN = "\033[2J"
    CLEAR_LINE = "\033[2K"
    MOVE_HOME = "\033[H"
    MOVE_UP = "\033[{}A"
    SAVE_CURSOR = "\033[s"
    RESTORE_CURSOR = "\033[u"

    # ── Spinner ──
    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    # ── State ──
    _enabled: bool = True
    _spinner_idx: int = 0
    _initialized: bool = False

    # ── Detection ──────────────────────────────────────────────────────────

    @classmethod
    def supports_color(cls) -> bool:
        """Check if the terminal supports ANSI color output."""
        if not sys.stdout.isatty():
            return False
        term = os.environ.get("TERM", "")
        if term == "dumb":
            return False
        # Check for NO_COLOR / FORCE_COLOR env vars (standard conventions)
        if os.environ.get("NO_COLOR"):
            return False
        return True

    @classmethod
    def init(cls, force: Optional[bool] = None):
        """Initialize terminal detection. Call once at module load or script start.

        Args:
            force: True to force-enable, False to force-disable, None for auto-detect.
        """
        if cls._initialized:
            return
        cls._initialized = True

        if force is True:
            cls._enabled = True
        elif force is False:
            cls._enabled = False
        else:
            cls._enabled = cls.supports_color()

        if not cls._enabled:
            cls._disable_colors()

    @classmethod
    def _disable_colors(cls):
        """Clear all ANSI escape sequences — disables all formatting."""
        for attr_name in dir(cls):
            if attr_name.startswith("_"):
                continue
            val = getattr(cls, attr_name)
            if isinstance(val, str) and val.startswith("\033"):
                setattr(cls, attr_name, "")

    @classmethod
    def spinner(cls) -> str:
        """Return the next spinner frame (cycling through SPINNER_FRAMES)."""
        if not cls._enabled:
            return ""
        frame = cls.SPINNER_FRAMES[cls._spinner_idx % len(cls.SPINNER_FRAMES)]
        cls._spinner_idx += 1
        return frame


# ── Convenience: strip ANSI ─────────────────────────────────────────────────

_ANSI_RE = re.compile(r"\033\[[0-9;]*[mK]")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences to get visible string length."""
    return _ANSI_RE.sub("", text)


# ── Auto-initialize on import ───────────────────────────────────────────────

Term.init()
