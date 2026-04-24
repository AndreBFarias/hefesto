"""Testes unitários para FEAT-RUMBLE-POLICY-01 — política de intensidade de rumble.

Cobre:
- Cada preset retorna mult correto.
- Modo Auto respeita battery thresholds (mock battery_pct 80/40/10).
- Debounce 5s evita flapping em modo auto.
- rumble.set(100, 200) com policy "economia" aplica (30, 60).
- RumbleEngine aplica mult via _apply_with_policy.
- _handle_rumble_policy_set e _handle_rumble_policy_custom do IPC.
"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from hefesto.core.rumble import RumbleEngine, _effective_mult
from hefesto.daemon.lifecycle import DaemonConfig

# AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01: _effective_mult_inline foi deletado;
# testes usam a função canônica _effective_mult. Alias local mantém os
# call sites curtos e legíveis sem alterar semântica dos asserts.
_effective_mult_inline = _effective_mult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config(policy: str, custom_mult: float = 0.7) -> DaemonConfig:
    cfg = DaemonConfig()
    cfg.rumble_policy = policy  # type: ignore[assignment]
    cfg.rumble_policy_custom_mult = custom_mult
    return cfg


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

class TestPresets:
    """Cada preset retorna o multiplicador esperado."""

    def test_economia(self) -> None:
        cfg = _config("economia")
        mult, _, _ = _effective_mult_inline(cfg, 100, 1.0, 0.7, 0.0)
        assert mult == pytest.approx(0.3)

    def test_balanceado(self) -> None:
        cfg = _config("balanceado")
        mult, _, _ = _effective_mult_inline(cfg, 100, 1.0, 0.7, 0.0)
        assert mult == pytest.approx(0.7)

    def test_max(self) -> None:
        cfg = _config("max")
        mult, _, _ = _effective_mult_inline(cfg, 100, 1.0, 0.7, 0.0)
        assert mult == pytest.approx(1.0)

    def test_custom(self) -> None:
        cfg = _config("custom", custom_mult=0.45)
        mult, _, _ = _effective_mult_inline(cfg, 100, 1.0, 0.7, 0.0)
        assert mult == pytest.approx(0.45)

    def test_custom_via_rumble_py(self) -> None:
        """Garante que a _effective_mult em rumble.py retorna igual."""
        cfg = _config("custom", custom_mult=0.55)
        mult, _, _ = _effective_mult(cfg, 80, 1.0, 0.7, 0.0)
        assert mult == pytest.approx(0.55)


# ---------------------------------------------------------------------------
# Modo Auto — thresholds de bateria
# ---------------------------------------------------------------------------

class TestAutoMode:
    """Modo auto respeita thresholds de bateria."""

    def test_bateria_alta(self) -> None:
        cfg = _config("auto")
        mult, new_last, _new_at = _effective_mult_inline(cfg, 80, 1.0, 0.7, 0.0)
        assert mult == pytest.approx(1.0)
        assert new_last == pytest.approx(1.0)

    def test_bateria_media(self) -> None:
        cfg = _config("auto")
        mult, _, _ = _effective_mult_inline(cfg, 40, 1.0, 1.0, 0.0)
        assert mult == pytest.approx(0.7)

    def test_bateria_baixa(self) -> None:
        cfg = _config("auto")
        mult, _, _ = _effective_mult_inline(cfg, 10, 1.0, 1.0, 0.0)
        assert mult == pytest.approx(0.3)

    def test_limiar_exato_50(self) -> None:
        """battery_pct == 50 deve retornar 0.7 (>50 para 1.0)."""
        cfg = _config("auto")
        mult, _, _ = _effective_mult_inline(cfg, 50, 1.0, 1.0, 0.0)
        assert mult == pytest.approx(0.7)

    def test_limiar_exato_51(self) -> None:
        cfg = _config("auto")
        mult, _, _ = _effective_mult_inline(cfg, 51, 1.0, 0.7, 0.0)
        assert mult == pytest.approx(1.0)

    def test_limiar_exato_20(self) -> None:
        """battery_pct == 20 deve retornar 0.7 (>=20 para 0.7)."""
        cfg = _config("auto")
        mult, _, _ = _effective_mult_inline(cfg, 20, 1.0, 1.0, 0.0)
        assert mult == pytest.approx(0.7)

    def test_limiar_exato_19(self) -> None:
        cfg = _config("auto")
        mult, _, _ = _effective_mult_inline(cfg, 19, 1.0, 1.0, 0.0)
        assert mult == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# Debounce do modo auto
# ---------------------------------------------------------------------------

class TestAutoDebounce:
    """Debounce de 5s evita flapping no modo auto."""

    def test_sem_debounce_muda(self) -> None:
        """Primeira mudança (last_change_at == 0.0) ocorre imediatamente."""
        cfg = _config("auto")
        # Começa sem debounce registrado (0.0).
        mult, new_last, new_at = _effective_mult_inline(cfg, 10, 100.0, 0.7, 0.0)
        assert mult == pytest.approx(0.3)
        assert new_last == pytest.approx(0.3)
        assert new_at == pytest.approx(100.0)

    def test_dentro_debounce_nao_muda(self) -> None:
        """Mudança dentro de 5s mantém mult anterior."""
        cfg = _config("auto")
        # bateria 10% -> mult alvo 0.3; mas debounce: last_change_at=100.0, now=102.0 (<5s).
        mult, new_last, new_at = _effective_mult_inline(
            cfg, 10, 102.0, 0.7, 100.0  # 2s desde mudança
        )
        assert mult == pytest.approx(0.7)  # mantém anterior
        assert new_last == pytest.approx(0.7)
        assert new_at == pytest.approx(100.0)  # timestamp não muda

    def test_apos_debounce_muda(self) -> None:
        """Mudança após 5s+ é aplicada."""
        cfg = _config("auto")
        mult, new_last, new_at = _effective_mult_inline(
            cfg, 10, 106.0, 0.7, 100.0  # 6s desde mudança
        )
        assert mult == pytest.approx(0.3)
        assert new_last == pytest.approx(0.3)
        assert new_at == pytest.approx(106.0)

    def test_sem_mudanca_mantem(self) -> None:
        """Se target == last_auto_mult, retorna estável sem debounce."""
        cfg = _config("auto")
        mult, new_last, new_at = _effective_mult_inline(
            cfg, 80, 200.0, 1.0, 100.0  # bateria 80% -> alvo 1.0 = current
        )
        assert mult == pytest.approx(1.0)
        assert new_last == pytest.approx(1.0)
        assert new_at == pytest.approx(100.0)  # timestamp não muda


# ---------------------------------------------------------------------------
# Integração: rumble.set com política
# ---------------------------------------------------------------------------

class TestRumbleSetComPolitica:
    """rumble.set(100, 200) com policy 'economia' aplica (30, 60)."""

    def test_economia_aplica_mult_30(self) -> None:
        controller = MagicMock()
        engine = RumbleEngine(controller, time_fn=lambda: 1.0)
        cfg = _config("economia")

        # Injeta referência ao config (sem state_ref — fallback para battery 50).
        engine.link(cfg, None)

        engine.set(100, 200)
        applied = engine.tick()

        assert applied is not None
        # 100 * 0.3 = 30, 200 * 0.3 = 60
        controller.set_rumble.assert_called_once_with(weak=30, strong=60)

    def test_balanceado_aplica_mult_70(self) -> None:
        controller = MagicMock()
        engine = RumbleEngine(controller, time_fn=lambda: 1.0)
        cfg = _config("balanceado")
        engine.link(cfg, None)

        engine.set(100, 100)
        engine.tick()

        # 100 * 0.7 = 70
        controller.set_rumble.assert_called_once_with(weak=70, strong=70)

    def test_max_sem_alteracao(self) -> None:
        controller = MagicMock()
        engine = RumbleEngine(controller, time_fn=lambda: 1.0)
        cfg = _config("max")
        engine.link(cfg, None)

        engine.set(100, 200)
        engine.tick()

        # 100 * 1.0 = 100, 200 * 1.0 = 200
        controller.set_rumble.assert_called_once_with(weak=100, strong=200)

    def test_clamp_resultado(self) -> None:
        """Resultado é clampado em [0, 255]."""
        controller = MagicMock()
        engine = RumbleEngine(controller, time_fn=lambda: 1.0)
        cfg = _config("max")
        engine.link(cfg, None)

        engine.set(255, 255)
        engine.tick()

        controller.set_rumble.assert_called_once_with(weak=255, strong=255)

    def test_sem_link_usa_mult_1(self) -> None:
        """Sem link(), engine aplica mult 1.0 (modo legacy)."""
        controller = MagicMock()
        engine = RumbleEngine(controller, time_fn=lambda: 1.0)

        engine.set(100, 200)
        engine.tick()

        controller.set_rumble.assert_called_once_with(weak=100, strong=200)

    def test_auto_com_bateria_baixa(self) -> None:
        """Modo auto + battery 10% -> mult 0.3."""
        controller = MagicMock()
        engine = RumbleEngine(controller, time_fn=lambda: 1.0)
        cfg = _config("auto")

        state_ref = MagicMock()
        state_ref.battery_pct = 10
        engine.link(cfg, state_ref)
        # Inicializa debounce como primeira mudança (last_change_at == 0.0).
        engine._last_auto_change_at = 0.0
        engine._last_auto_mult = 0.7

        engine.set(100, 200)
        engine.tick()

        # 100 * 0.3 = 30, 200 * 0.3 = 60
        controller.set_rumble.assert_called_once_with(weak=30, strong=60)


# ---------------------------------------------------------------------------
# IPC handlers
# ---------------------------------------------------------------------------

class TestIpcHandlers:
    """_handle_rumble_policy_set e _handle_rumble_policy_custom."""

    def _make_server(self) -> object:
        """Cria IpcServer com config de daemon mockado."""
        from hefesto.daemon.ipc_server import IpcServer
        from hefesto.daemon.state_store import StateStore

        ctrl = MagicMock()
        store = StateStore()
        store.update_controller_state(MagicMock(battery_pct=80))
        pm = MagicMock()

        daemon_cfg = DaemonConfig()
        daemon = MagicMock()
        daemon.config = daemon_cfg
        daemon.store = store

        server = IpcServer(
            controller=ctrl,
            store=store,
            profile_manager=pm,
            daemon=daemon,
        )
        return server, daemon_cfg

    def test_policy_set_valida(self) -> None:
        server, cfg = self._make_server()
        result = asyncio.run(server._handle_rumble_policy_set({"policy": "economia"}))
        assert result == {"status": "ok", "policy": "economia"}
        assert cfg.rumble_policy == "economia"

    def test_policy_set_invalida(self) -> None:
        server, _cfg = self._make_server()
        with pytest.raises(ValueError, match="deve ser um de"):
            asyncio.run(server._handle_rumble_policy_set({"policy": "turbinado"}))

    def test_policy_custom(self) -> None:
        server, cfg = self._make_server()
        result = asyncio.run(server._handle_rumble_policy_custom({"mult": 0.45}))
        assert result == {"status": "ok", "mult": pytest.approx(0.45)}
        assert cfg.rumble_policy == "custom"
        assert cfg.rumble_policy_custom_mult == pytest.approx(0.45)

    def test_policy_custom_fora_de_range(self) -> None:
        server, _cfg = self._make_server()
        with pytest.raises(ValueError, match="fora de"):
            asyncio.run(server._handle_rumble_policy_custom({"mult": 1.5}))

    def test_policy_auto(self) -> None:
        server, cfg = self._make_server()
        result = asyncio.run(server._handle_rumble_policy_set({"policy": "auto"}))
        assert result["policy"] == "auto"
        assert cfg.rumble_policy == "auto"

    def test_state_full_inclui_rumble_policy(self) -> None:
        """daemon.state_full retorna rumble_policy no payload."""
        server, _cfg = self._make_server()

        snap_ctrl = MagicMock()
        snap_ctrl.connected = True
        snap_ctrl.transport = "usb"
        snap_ctrl.battery_pct = 80
        snap_ctrl.l2_raw = 0
        snap_ctrl.r2_raw = 0
        snap_ctrl.raw_lx = 128
        snap_ctrl.raw_ly = 128
        snap_ctrl.raw_rx = 128
        snap_ctrl.raw_ry = 128

        snap = MagicMock()
        snap.controller = snap_ctrl
        snap.active_profile = "default"
        snap.counters = {}

        server.store = MagicMock()
        server.store.snapshot.return_value = snap

        result = asyncio.run(server._handle_daemon_state_full({}))
        assert "rumble_policy" in result
        assert result["rumble_policy"] == "balanceado"
        assert "rumble_policy_custom_mult" in result
        assert "rumble_mult_applied" in result


# ---------------------------------------------------------------------------
# Encapsulamento: RumbleEngine.update_auto_state
# ---------------------------------------------------------------------------

class TestUpdateAutoState:
    """AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01 — método público substitui
    writeback direto de campos privados por chamadores externos.
    """

    def test_atualiza_campos_auto_e_mult_applied_default(self) -> None:
        """Sem mult_applied explícito, usa auto_mult nos três campos."""
        controller = MagicMock()
        engine = RumbleEngine(controller)
        engine.update_auto_state(0.3, 123.0)
        assert engine._last_auto_mult == pytest.approx(0.3)
        assert engine._last_auto_change_at == pytest.approx(123.0)
        assert engine.last_mult_applied == pytest.approx(0.3)

    def test_mult_applied_explicito_difere_de_auto_mult(self) -> None:
        """Policies fixas: mult efetivo aplicado difere do auto debounce state."""
        controller = MagicMock()
        engine = RumbleEngine(controller)
        # Simula auto debounce em 0.7 mas policy fixa 'economia' aplicando 0.3.
        engine.update_auto_state(0.7, 200.0, mult_applied=0.3)
        assert engine._last_auto_mult == pytest.approx(0.7)
        assert engine._last_auto_change_at == pytest.approx(200.0)
        assert engine.last_mult_applied == pytest.approx(0.3)

    def test_substitui_writeback_direto(self) -> None:
        """Prova funcional: mesmo efeito que o writeback direto antigo."""
        controller = MagicMock()
        engine_a = RumbleEngine(controller)
        engine_b = RumbleEngine(controller)

        # Método público (novo).
        engine_a.update_auto_state(1.0, 42.5, mult_applied=0.55)

        # Writeback direto (antigo — agora proibido fora de core/rumble.py).
        engine_b._last_auto_mult = 1.0
        engine_b._last_auto_change_at = 42.5
        engine_b._last_mult_applied = 0.55

        assert engine_a._last_auto_mult == engine_b._last_auto_mult
        assert engine_a._last_auto_change_at == engine_b._last_auto_change_at
        assert engine_a.last_mult_applied == engine_b.last_mult_applied


# ---------------------------------------------------------------------------
# FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01 — override de policy por perfil
# ---------------------------------------------------------------------------


class TestProfileOverride:
    """`_effective_mult` aceita `profile_override` keyword-only opcional.

    Override tem precedência sobre config global quando presente e não-None.
    """

    def test_override_none_usa_global(self) -> None:
        """Perfil sem policy definido -> herda `config.rumble_policy`."""
        from hefesto.profiles.schema import RumbleConfig

        cfg = _config("max")
        override = RumbleConfig()  # policy=None default
        mult, _, _ = _effective_mult(
            cfg, 100, 1.0, 0.7, 0.0, profile_override=override
        )
        assert mult == pytest.approx(1.0)  # lido do global "max"

    def test_override_economia_sobrescreve_global_max(self) -> None:
        """`config="max"` + `override.policy="economia"` -> mult 0.3."""
        from hefesto.profiles.schema import RumbleConfig

        cfg = _config("max")
        override = RumbleConfig(policy="economia")
        mult, _, _ = _effective_mult(
            cfg, 100, 1.0, 0.7, 0.0, profile_override=override
        )
        assert mult == pytest.approx(0.3)

    def test_override_custom_usa_policy_custom_mult_do_perfil(self) -> None:
        """`override.policy='custom'` + `policy_custom_mult=1.5` -> mult 1.5.

        NÃO lê `config.rumble_policy_custom_mult` (0.7) — custom do perfil
        ganha. Se lesse do config, mult seria 0.7.
        """
        from hefesto.profiles.schema import RumbleConfig

        cfg = _config("balanceado", custom_mult=0.7)
        override = RumbleConfig(policy="custom", policy_custom_mult=1.5)
        mult, _, _ = _effective_mult(
            cfg, 100, 1.0, 0.7, 0.0, profile_override=override
        )
        assert mult == pytest.approx(1.5)

    def test_override_auto_preserva_debounce_state(self) -> None:
        """`override.policy='auto'` + battery 10% -> mult 0.3; debounce ok."""
        from hefesto.profiles.schema import RumbleConfig

        cfg = _config("max")
        override = RumbleConfig(policy="auto")
        mult, new_last, new_at = _effective_mult(
            cfg, 10, 100.0, 0.7, 0.0, profile_override=override
        )
        assert mult == pytest.approx(0.3)
        assert new_last == pytest.approx(0.3)
        assert new_at == pytest.approx(100.0)

    def test_override_policy_fixa_ignora_custom_mult_do_perfil(self) -> None:
        """Para policy!=custom, `policy_custom_mult` do perfil é ignorado.

        Guarda contra regressão semântica: usuário configurando perfil com
        `policy='economia'` + `policy_custom_mult=1.99` (sem sentido) não
        corrompe o mult — 'economia' ainda retorna 0.3 da tabela fixa.
        """
        from hefesto.profiles.schema import RumbleConfig

        cfg = _config("max")
        override = RumbleConfig(policy="economia", policy_custom_mult=1.99)
        mult, _, _ = _effective_mult(
            cfg, 100, 1.0, 0.7, 0.0, profile_override=override
        )
        assert mult == pytest.approx(0.3)


class TestEngineProfileOverride:
    """`RumbleEngine._compute_mult` le override via ProfileManager linkado."""

    def test_engine_compute_mult_le_override_do_profile_manager(self) -> None:
        """`link(config, state, profile_manager=pm)` com override economia.

        `config.rumble_policy='max'`, perfil ativo com `policy='economia'`:
        engine deve retornar 0.3 (override ganha do global).
        """
        from unittest.mock import MagicMock

        from hefesto.profiles.schema import RumbleConfig

        controller = MagicMock()
        engine = RumbleEngine(controller, time_fn=lambda: 1.0)
        cfg = _config("max")

        # Mock de ProfileManager com get_active_rumble_config retornando override.
        pm = MagicMock()
        pm.get_active_rumble_config.return_value = RumbleConfig(policy="economia")

        engine.link(cfg, None, profile_manager=pm)
        engine.set(100, 200)
        engine.tick()

        # Hardware deve ter recebido mult 0.3 aplicado: weak=30, strong=60.
        controller.set_rumble.assert_called_once_with(weak=30, strong=60)
        assert engine.last_mult_applied == pytest.approx(0.3)

    def test_engine_sem_profile_manager_mantem_comportamento(self) -> None:
        """`link(config, state)` sem `profile_manager` preserva semantica pré-sprint.

        Compatibilidade: testes existentes que chamam `link(cfg, None)` sem o
        kwarg novo continuam lendo de `config.rumble_policy` normalmente.
        """
        from unittest.mock import MagicMock

        controller = MagicMock()
        engine = RumbleEngine(controller, time_fn=lambda: 1.0)
        cfg = _config("economia")

        engine.link(cfg, None)  # sem profile_manager (default None)
        engine.set(100, 200)
        engine.tick()

        # Mult 0.3 lido do global "economia": weak=30, strong=60.
        controller.set_rumble.assert_called_once_with(weak=30, strong=60)

    def test_engine_override_none_no_manager_usa_global(self) -> None:
        """`profile_manager.get_active_rumble_config()` retorna None -> usa global."""
        from unittest.mock import MagicMock

        controller = MagicMock()
        engine = RumbleEngine(controller, time_fn=lambda: 1.0)
        cfg = _config("max")

        pm = MagicMock()
        pm.get_active_rumble_config.return_value = None

        engine.link(cfg, None, profile_manager=pm)
        engine.set(100, 200)
        engine.tick()

        # Mult 1.0 do global "max": weak=100, strong=200.
        controller.set_rumble.assert_called_once_with(weak=100, strong=200)


class TestReassertRumbleOverride:
    """`reassert_rumble` propaga override do perfil ativo via daemon._profile_manager."""

    def test_reassert_rumble_usa_override_do_perfil(self) -> None:
        """`daemon._profile_manager.get_active_rumble_config` retorna override economia.

        `config.rumble_policy='max'`, override='economia':
        `set_rumble` recebe valores multiplicados por 0.3 (não 1.0).
        """
        from unittest.mock import MagicMock

        from hefesto.daemon.subsystems.rumble import reassert_rumble
        from hefesto.profiles.schema import RumbleConfig

        controller = MagicMock()
        store = MagicMock()
        snap = MagicMock()
        snap.controller = MagicMock(battery_pct=80)
        store.snapshot.return_value = snap

        cfg = _config("max")
        cfg.rumble_active = (100, 200)

        pm = MagicMock()
        pm.get_active_rumble_config.return_value = RumbleConfig(policy="economia")

        daemon = MagicMock()
        daemon.config = cfg
        daemon.store = store
        daemon.controller = controller
        daemon._profile_manager = pm
        daemon._last_auto_mult = 0.7
        daemon._last_auto_change_at = 0.0

        reassert_rumble(daemon, now=1.0)

        # Mult 0.3 aplicado -> 100*0.3=30, 200*0.3=60.
        controller.set_rumble.assert_called_once_with(weak=30, strong=60)

    def test_reassert_rumble_sem_profile_manager_usa_global(self) -> None:
        """Sem `_profile_manager` no daemon, comportamento pré-sprint preservado."""
        from unittest.mock import MagicMock

        from hefesto.daemon.subsystems.rumble import reassert_rumble

        controller = MagicMock()
        store = MagicMock()
        snap = MagicMock()
        snap.controller = MagicMock(battery_pct=80)
        store.snapshot.return_value = snap

        cfg = _config("economia")
        cfg.rumble_active = (100, 200)

        daemon = MagicMock(spec=["config", "store", "controller",
                                  "_last_auto_mult", "_last_auto_change_at"])
        daemon.config = cfg
        daemon.store = store
        daemon.controller = controller
        daemon._last_auto_mult = 0.7
        daemon._last_auto_change_at = 0.0

        reassert_rumble(daemon, now=1.0)

        # Mult 0.3 do global "economia" -> 100*0.3=30, 200*0.3=60.
        controller.set_rumble.assert_called_once_with(weak=30, strong=60)

    def test_apply_rumble_policy_usa_override_do_perfil(self) -> None:
        """`apply_rumble_policy` (IPC rumble.set) tambem respeita override."""
        from unittest.mock import MagicMock

        from hefesto.daemon.ipc_rumble_policy import apply_rumble_policy
        from hefesto.profiles.schema import RumbleConfig

        cfg = _config("max")

        pm = MagicMock()
        pm.get_active_rumble_config.return_value = RumbleConfig(
            policy="custom", policy_custom_mult=0.5
        )

        store = MagicMock()
        snap = MagicMock()
        snap.controller = MagicMock(battery_pct=80)
        store.snapshot.return_value = snap

        daemon = MagicMock()
        daemon.config = cfg
        daemon.store = store
        daemon._profile_manager = pm
        daemon._rumble_engine = None

        eff_weak, eff_strong = apply_rumble_policy(daemon, 100, 200)

        # Mult 0.5 do perfil custom -> 50, 100.
        assert eff_weak == 50
        assert eff_strong == 100


# ---------------------------------------------------------------------------
# FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01 — JSONs default não definem override
# ---------------------------------------------------------------------------


def test_profiles_default_nao_definem_policy_override() -> None:
    """Todos os JSONs em assets/profiles_default/ mantêm `policy` None.

    Sprint não modifica arquivos default; teste garante que nenhum foi
    tocado por acidente (critério #11 do spec).
    """
    import json
    from pathlib import Path

    defaults_dir = (
        Path(__file__).resolve().parent.parent.parent
        / "assets"
        / "profiles_default"
    )
    assert defaults_dir.is_dir(), f"diretório não encontrado: {defaults_dir}"

    json_files = sorted(defaults_dir.glob("*.json"))
    assert len(json_files) > 0, "esperava ao menos 1 perfil default"

    for json_path in json_files:
        with json_path.open(encoding="utf-8") as f:
            data = json.load(f)
        rumble = data.get("rumble", {})
        assert rumble.get("policy") is None, (
            f"{json_path.name}: rumble.policy deveria ser None/ausente, "
            f"encontrou {rumble.get('policy')!r}"
        )
        assert rumble.get("policy_custom_mult") is None, (
            f"{json_path.name}: rumble.policy_custom_mult deveria ser None/ausente, "
            f"encontrou {rumble.get('policy_custom_mult')!r}"
        )
