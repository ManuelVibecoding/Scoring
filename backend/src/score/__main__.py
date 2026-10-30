"""Permite correr el pipeline con `python -m score ...` (sin depender de score.exe)."""

from score.entrypoints.cli import main

raise SystemExit(main())
