"""IO de presets standalone de gatilho (FEAT-TRIGGER-PRESETS-IMPORT-EXPORT-01).

Funções utilitárias puras (sem GTK, sem IPC) para serializar e desserializar
um ``TriggerPreset`` em arquivo ``.json``.

Atomic write via ``tempfile + replace``, espelhando o padrão de
``hefesto.profiles.manager.save_profile``: grava em ``<path>.tmp``, depois
renomeia para ``<path>``. Falha entre os dois passos não corrompe o arquivo
final.

Não engole exceções — quem chama (handler GTK ou teste) decide o formato
da mensagem ao usuário.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from hefesto.profiles.schema import TriggerConfig
from hefesto.profiles.trigger_preset_schema import SCHEMA_VERSION, TriggerPreset


def export_trigger_preset(
    path: Path | str,
    *,
    name: str,
    trigger: TriggerConfig,
) -> Path:
    """Serializa ``trigger`` como ``TriggerPreset`` JSON em ``path``.

    Garante extensão ``.json``: se o caminho recebido tiver extensão diferente
    ou ausente, troca/adiciona ``.json`` antes de gravar.

    Atomic write: escreve em ``<final>.tmp`` e usa ``Path.replace`` para
    posicionar o arquivo final. Se a escrita do tmp falhar, o arquivo final
    não é tocado.

    Retorna o ``Path`` final (validado e com sufixo correto).
    """
    preset = TriggerPreset(
        schema_version=SCHEMA_VERSION,
        name=name,
        exported_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        trigger=trigger,
    )
    payload = preset.model_dump(mode="json")
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)

    final_path = Path(path)
    if final_path.suffix != ".json":
        final_path = final_path.with_suffix(".json")

    tmp_path = final_path.with_suffix(".json.tmp")
    tmp_path.write_text(text + "\n", encoding="utf-8")
    tmp_path.replace(final_path)
    return final_path


def import_trigger_preset(path: Path | str) -> TriggerPreset:
    """Lê e valida JSON em ``path`` retornando ``TriggerPreset``.

    Levanta:
        FileNotFoundError: arquivo inexistente.
        json.JSONDecodeError: JSON malformado.
        pydantic.ValidationError: schema rejeitou (campo ausente, valor
            inválido, ``schema_version`` desconhecida, ``extra="forbid"``).
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return TriggerPreset.model_validate(raw)


__all__ = ["export_trigger_preset", "import_trigger_preset"]
