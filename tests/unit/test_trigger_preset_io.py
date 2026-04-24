"""Testes unitários do IO standalone de preset de gatilho.

FEAT-TRIGGER-PRESETS-IMPORT-EXPORT-01.

Cobertura:
  - Round-trip simples (Rigid).
  - Round-trip aninhado (MultiPositionFeedback com ``params: list[list[int]]``).
  - Normalização de extensão (path sem ``.json`` ganha sufixo).
  - Escrita atômica (tmp + replace) — falha entre tmp e replace não cria final.
  - JSON malformado levanta ``json.JSONDecodeError``.
  - schema_version inválido levanta ``ValidationError``.
  - name vazio levanta ``ValidationError``.
  - exported_at malformado levanta ``ValidationError``.
  - extra field levanta ``ValidationError`` (``extra="forbid"``).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hefesto.profiles.schema import TriggerConfig
from hefesto.profiles.trigger_preset_io import (
    export_trigger_preset,
    import_trigger_preset,
)
from hefesto.profiles.trigger_preset_schema import SCHEMA_VERSION, TriggerPreset


def test_round_trip_simples(tmp_path: Path) -> None:
    cfg = TriggerConfig(mode="Rigid", params=[0, 255])
    final = export_trigger_preset(tmp_path / "rigid.json", name="Rigid teste", trigger=cfg)
    assert final.exists()
    preset = import_trigger_preset(final)
    assert preset.trigger == cfg
    assert preset.name == "Rigid teste"
    assert preset.schema_version == SCHEMA_VERSION


def test_round_trip_aninhado(tmp_path: Path) -> None:
    nested = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 0]]
    cfg = TriggerConfig(mode="MultiPositionFeedback", params=nested)
    final = export_trigger_preset(
        tmp_path / "multipos.json", name="Multi pos arco", trigger=cfg
    )
    preset = import_trigger_preset(final)
    assert preset.trigger.mode == "MultiPositionFeedback"
    assert preset.trigger.params == nested
    assert preset.trigger.is_nested is True


def test_export_normaliza_extensao(tmp_path: Path) -> None:
    cfg = TriggerConfig(mode="Off", params=[])
    final = export_trigger_preset(tmp_path / "sem_extensao", name="Off", trigger=cfg)
    assert final.suffix == ".json"
    assert final.name == "sem_extensao.json"
    assert final.exists()


def test_export_substitui_extensao_nao_json(tmp_path: Path) -> None:
    cfg = TriggerConfig(mode="Off", params=[])
    final = export_trigger_preset(tmp_path / "preset.txt", name="Off", trigger=cfg)
    assert final.suffix == ".json"
    assert final.exists()


def test_export_atomic_write_tmp_nao_persiste(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Se ``replace`` falha, ``<final>`` original não é sobrescrito."""
    cfg = TriggerConfig(mode="Rigid", params=[0, 255])
    target = tmp_path / "atomic.json"

    # Pré-grava conteúdo válido em ``target`` para confirmar invariante de
    # "se replace falhar, conteúdo antigo permanece".
    target.write_text('{"preexistente": true}\n', encoding="utf-8")
    conteudo_antigo = target.read_text(encoding="utf-8")

    # Patch ``Path.replace`` para levantar OSError simulando falha de IO.
    original_replace = Path.replace

    def replace_falho(self: Path, target_path: Path | str) -> Path:
        if str(self).endswith(".json.tmp"):
            raise OSError("falha simulada em replace")
        return original_replace(self, target_path)

    monkeypatch.setattr(Path, "replace", replace_falho)

    with pytest.raises(OSError, match="falha simulada"):
        export_trigger_preset(target, name="atomic", trigger=cfg)

    # Arquivo final intocado.
    assert target.read_text(encoding="utf-8") == conteudo_antigo
    # Tmp pode ter sido escrito mas não promovido a final.
    tmp_path_file = target.with_suffix(".json.tmp")
    if tmp_path_file.exists():
        # Conteúdo do tmp deve ser o do preset novo, garantindo atomicidade.
        assert "atomic" in tmp_path_file.read_text(encoding="utf-8")


def test_import_json_malformado_levanta_decodeerror(tmp_path: Path) -> None:
    target = tmp_path / "ruim.json"
    target.write_text("{invalido", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        import_trigger_preset(target)


def test_import_schema_version_invalido_levanta_validation(tmp_path: Path) -> None:
    target = tmp_path / "v999.json"
    raw = {
        "schema_version": 999,
        "name": "qualquer",
        "exported_at": "2026-04-24T00:00:00+00:00",
        "trigger": {"mode": "Off", "params": []},
    }
    target.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValidationError):
        import_trigger_preset(target)


def test_import_name_vazio_levanta_validation(tmp_path: Path) -> None:
    target = tmp_path / "sem_nome.json"
    raw = {
        "schema_version": 1,
        "name": "",
        "exported_at": "2026-04-24T00:00:00+00:00",
        "trigger": {"mode": "Off", "params": []},
    }
    target.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValidationError):
        import_trigger_preset(target)


def test_import_exported_at_invalido_levanta_validation(tmp_path: Path) -> None:
    target = tmp_path / "ts_ruim.json"
    raw = {
        "schema_version": 1,
        "name": "ok",
        "exported_at": "ontem-de-tarde",
        "trigger": {"mode": "Off", "params": []},
    }
    target.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValidationError):
        import_trigger_preset(target)


def test_import_extra_field_levanta_validation(tmp_path: Path) -> None:
    target = tmp_path / "extra.json"
    raw = {
        "schema_version": 1,
        "name": "ok",
        "exported_at": "2026-04-24T00:00:00+00:00",
        "trigger": {"mode": "Off", "params": []},
        "campo_extra": "proibido",
    }
    target.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValidationError):
        import_trigger_preset(target)


def test_import_arquivo_inexistente_levanta_filenotfound(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        import_trigger_preset(tmp_path / "nao_existe.json")


def test_export_grava_iso8601_com_timezone(tmp_path: Path) -> None:
    cfg = TriggerConfig(mode="Off", params=[])
    final = export_trigger_preset(tmp_path / "ts.json", name="ts", trigger=cfg)
    raw = json.loads(final.read_text(encoding="utf-8"))
    ts = raw["exported_at"]
    assert ts.endswith("+00:00") or ts.endswith("Z")
    # Reparseável.
    from datetime import datetime
    datetime.fromisoformat(ts)


def test_preset_model_round_trip_dump_validate() -> None:
    """Sanidade: ``model_dump(mode='json')`` -> ``model_validate`` é idempotente."""
    preset = TriggerPreset(
        schema_version=1,
        name="abc",
        exported_at="2026-04-24T00:00:00+00:00",
        trigger=TriggerConfig(mode="Off", params=[]),
    )
    raw = preset.model_dump(mode="json")
    preset2 = TriggerPreset.model_validate(raw)
    assert preset2 == preset
