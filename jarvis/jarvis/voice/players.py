"""Locate a command-line audio player that can play MP3 from stdin or a file."""
from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Player:
    name: str
    stdin_cmd: list[str] | None  # command that reads MP3 from stdin, or None
    file_cmd: list[str]          # command that plays a file path appended at the end

    @property
    def streams(self) -> bool:
        return self.stdin_cmd is not None


_CANDIDATES: list[Player] = [
    Player("ffplay", ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-i", "pipe:0"],
           ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]),
    Player("mpv", ["mpv", "--no-video", "--really-quiet", "-"], ["mpv", "--no-video", "--really-quiet"]),
    Player("mpg123", ["mpg123", "-q", "-"], ["mpg123", "-q"]),
    Player("afplay", None, ["afplay"]),          # macOS: file only
    Player("cvlc", None, ["cvlc", "--play-and-exit", "--quiet"]),
]


def find_player(override: str = "") -> Player | None:
    """Return the first available player, honouring an explicit override command."""
    if override.strip():
        cmd = shlex.split(override)
        streams = any(tok in {"-", "pipe:0", "/dev/stdin"} for tok in cmd)
        return Player(Path(cmd[0]).name, cmd if streams else None, [t for t in cmd if t not in {"-", "pipe:0"}])
    for cand in _CANDIDATES:
        if shutil.which(cand.file_cmd[0]):
            return cand
    if sys.platform == "win32":  # pragma: no cover - platform specific
        return Player(
            "powershell", None,
            ["powershell", "-NoProfile", "-Command",
             "Add-Type -AssemblyName presentationCore; $p = New-Object System.Windows.Media.MediaPlayer; "
             "$p.Open([uri]$args[0]); $p.Play(); Start-Sleep -Seconds 1; while($p.NaturalDuration.HasTimeSpan -and "
             "$p.Position -lt $p.NaturalDuration.TimeSpan){Start-Sleep -Milliseconds 200}"],
        )
    return None


def play_file(player: Player, path: Path) -> None:
    subprocess.run([*player.file_cmd, str(path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
