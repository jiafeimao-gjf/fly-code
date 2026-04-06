"""Logging utilities for fly-code."""

import sys
import os
from datetime import datetime
from enum import Enum
from pathlib import Path


class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"


# Check if terminal supports colors
def supports_color() -> bool:
    """Check if terminal supports ANSI colors."""
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    # On Windows, check for ANSI support
    if sys.platform == "win32":
        return os.environ.get("TERM") == "xterm"
    return True


USE_COLOR = supports_color()


def colorize(text: str, color: str) -> str:
    """Apply color to text if colors are supported."""
    if USE_COLOR:
        return f"{color}{text}{Colors.RESET}"
    return text


class Logger:
    """Enhanced logger for fly-code CLI with color and formatting."""

    def __init__(self, level: LogLevel = LogLevel.INFO, log_file: Path | None = None):
        self.level = level
        self.log_file = log_file
        self._file_handle = None

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            self._file_handle = open(log_file, "a", encoding="utf-8")

    def _format(self, level: str, msg: str, color: str = "") -> str:
        """Format a log message with timestamp and color."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_str = f"[{level}]"

        if USE_COLOR and color:
            formatted = f"{Colors.DIM}{timestamp}{Colors.RESET} {color}{level_str}{Colors.RESET} {msg}"
        else:
            formatted = f"{timestamp} [{level}] {msg}"

        return formatted

    def _log(self, level: LogLevel, msg: str, color: str = "", file: bool = True) -> None:
        """Internal log method."""
        if self.level.value > level.value:
            return

        formatted = self._format(level.name, msg, color)
        print(formatted)

        if file and self._file_handle:
            # Write plain text to file (no ANSI codes)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plain = f"{timestamp} [{level.name}] {msg}\n"
            self._file_handle.write(plain)
            self._file_handle.flush()

    def debug(self, msg: str) -> None:
        self._log(LogLevel.DEBUG, msg, Colors.DIM)

    def info(self, msg: str) -> None:
        self._log(LogLevel.INFO, msg, Colors.CYAN)

    def success(self, msg: str) -> None:
        """Log a success message in green."""
        self._log(LogLevel.INFO, msg, Colors.GREEN)

    def warning(self, msg: str) -> None:
        self._log(LogLevel.WARNING, msg, Colors.YELLOW)

    def error(self, msg: str) -> None:
        self._log(LogLevel.ERROR, msg, Colors.RED)

    def section(self, title: str) -> None:
        """Print a section header."""
        if USE_COLOR:
            line = "─" * (60 - len(title) - 2)
            print(f"\n{Colors.BOLD}{Colors.CYAN} {title} {line}{Colors.RESET}\n")
        else:
            print(f"\n=== {title} ===\n")

    def close(self) -> None:
        """Close log file if open."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None


# Default logger instance
logger = Logger()

# Global log file path (can be set by user)
LOG_DIR = Path.home() / ".fly-code" / "logs"


def setup_file_logging(enabled: bool = True) -> None:
    """Enable file logging to ~/.fly-code/logs/."""
    if enabled:
        log_file = LOG_DIR / f"fly-code-{datetime.now().strftime('%Y%m%d')}.log"
        global logger
        logger = Logger(log_file=log_file)
    else:
        logger = Logger()
