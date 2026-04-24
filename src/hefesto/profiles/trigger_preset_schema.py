"""Schema standalone de preset de gatilho exportável (FEAT-TRIGGER-PRESETS-IMPORT-EXPORT-01).

Diferença em relação a ``trigger_presets.py`` (sem sufixo ``_schema``):

- ``trigger_presets.py``: dicionários hardcoded de 10 intensidades por
  posição (``FEEDBACK_POSITION_PRESETS`` / ``VIBRATION_POSITION_PRESETS``).
  São presets internos do app, usados pelo combo "Preset por posição"
  da aba Gatilhos. Nunca vão a arquivo do usuário.
- Este módulo (``trigger_preset_schema.py``): wrapper JSON
  exportável/importável pelo usuário via GUI. Carrega metadados
  (versão, timestamp, nome legível) + um único ``TriggerConfig``.

Formato canônico em disco::

    {
      "schema_version": 1,
      "name": "Arco bow precisão",
      "exported_at": "2026-04-24T12:34:56+00:00",
      "trigger": {"mode": "MultiPositionFeedback", "params": [...]}
    }

Compat de migração: ``schema_version`` é validado de forma estrita.
Quando o formato evoluir, a versão sobe e ``_check_version`` ganha
ramo de upcast a partir do número antigo.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from hefesto.profiles.schema import TriggerConfig

SCHEMA_VERSION = 1


class TriggerPreset(BaseModel):
    """Preset standalone exportável de um único gatilho (L2 ou R2)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=SCHEMA_VERSION)
    name: str = Field(min_length=1, max_length=120)
    exported_at: str
    trigger: TriggerConfig

    @field_validator("schema_version")
    @classmethod
    def _check_version(cls, value: int) -> int:
        if value != SCHEMA_VERSION:
            raise ValueError(
                f"schema_version não suportado: {value} (esperado {SCHEMA_VERSION})"
            )
        return value

    @field_validator("exported_at")
    @classmethod
    def _check_timestamp(cls, value: str) -> str:
        if not value:
            raise ValueError("exported_at vazio")
        try:
            datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"exported_at não é ISO8601: {value}") from exc
        return value

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name vazio após strip")
        return stripped


__all__ = ["SCHEMA_VERSION", "TriggerPreset"]
