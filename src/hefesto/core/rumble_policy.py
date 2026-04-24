"""Alias de tipo `RumblePolicy` compartilhado entre daemon, schema e engine.

Extraido do `Literal` inline em `daemon/lifecycle.py` durante
FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01 para permitir reuso no schema
(`profiles/schema.py::RumbleConfig.policy`) sem gerar ciclo de import.

Modulo intencionalmente puro: zero dependencias internas do projeto.
"""
from __future__ import annotations

from typing import Literal

RumblePolicy = Literal["economia", "balanceado", "max", "auto", "custom"]

__all__ = ["RumblePolicy"]
