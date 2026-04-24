"""Motor de rumble com throttle anti-spam e política de intensidade.

Rumble passado do jogo (via UDP ou passthrough) pode chegar a centenas de
Hz. Aplicar cada atualização esgota a bateria, satura o motor HID e
deteriora os motors pequenos do DualSense. `RumbleEngine` agrupa os
comandos recebidos numa janela curta e aplica só o último a cada tick
de saída.

FEAT-RUMBLE-POLICY-01: política de intensidade global (economia/balanceado/
max/auto/custom) aplica multiplicador sobre weak e strong antes de enviar ao
hardware. O multiplicador do modo "auto" usa a bateria do estado mais recente
com debounce de 5s para evitar oscilação em limiar de threshold.

Uso:
    engine = RumbleEngine(controller, min_interval_sec=0.02)
    engine.set(weak=80, strong=150)    # pode ser chamado 1000x/s
    # tick() é chamado pelo poll loop do daemon e aplica se janela
    # estourou. Também aplica automaticamente quando weak+strong cai
    # para 0 (garantir desligamento imediato).
"""
from __future__ import annotations

import contextlib
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from hefesto.core.controller import IController
from hefesto.utils.logging_config import get_logger

if TYPE_CHECKING:
    from hefesto.daemon.lifecycle import DaemonConfig
    from hefesto.profiles.manager import ProfileManager
    from hefesto.profiles.schema import RumbleConfig

logger = get_logger(__name__)

DEFAULT_MIN_INTERVAL_SEC = 0.02  # 50Hz ceiling para motores HID
RUMBLE_MIN = 0
RUMBLE_MAX = 255


@dataclass
class RumbleCommand:
    weak: int
    strong: int

    def is_stop(self) -> bool:
        return self.weak == 0 and self.strong == 0


def _effective_mult(
    config: DaemonConfig,
    battery_pct: int,
    now: float,
    last_auto_mult: float,
    last_auto_change_at: float,
    auto_debounce_sec: float = 5.0,
    *,
    profile_override: RumbleConfig | None = None,
) -> tuple[float, float, float]:
    """Calcula multiplicador efetivo conforme política do config.

    Retorna (mult, novo_last_auto_mult, novo_last_auto_change_at).
    Os dois últimos valores devem ser guardados no estado do chamador
    para o debounce do modo "auto" funcionar corretamente entre chamadas.

    Modo "auto":
      - bateria >50% -> mult 1.0 (Máximo)
      - bateria 20-50% -> mult 0.7 (Balanceado)
      - bateria <20% -> mult 0.3 (Economia)
      Com debounce de `auto_debounce_sec` para evitar oscilação.

    FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01: quando `profile_override` é fornecido
    e seu `policy` não é None, sobrescreve `config.rumble_policy`. Para
    policy="custom", o `policy_custom_mult` lido vem do próprio perfil. Para
    policies fixas (economia/balanceado/max/auto), apenas o nome é lido do
    perfil; `policy_custom_mult` do perfil é ignorado nesse caso.
    """
    from hefesto.daemon.lifecycle import RUMBLE_POLICY_MULT

    # FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01: override por perfil tem precedência
    # sobre config global quando presente. Quando perfil não define policy,
    # herdamos o global (comportamento pré-sprint preservado).
    if profile_override is not None and profile_override.policy is not None:
        policy = profile_override.policy
        if policy == "custom":
            # Para custom, mult do perfil; validator já garante que não é None.
            custom_mult_source = profile_override.policy_custom_mult
        else:
            custom_mult_source = config.rumble_policy_custom_mult
    else:
        policy = config.rumble_policy
        custom_mult_source = config.rumble_policy_custom_mult

    if policy == "custom":
        mult = float(custom_mult_source) if custom_mult_source is not None else 0.7
        return mult, last_auto_mult, last_auto_change_at

    if policy in RUMBLE_POLICY_MULT:
        mult = RUMBLE_POLICY_MULT[policy]
        return mult, last_auto_mult, last_auto_change_at

    if policy == "auto":
        # Calcula mult alvo baseado em bateria.
        if battery_pct > 50:
            target = 1.0
        elif battery_pct >= 20:
            target = 0.7
        else:
            target = 0.3

        # Debounce: só muda se transcorreu tempo suficiente desde a última mudança.
        if target != last_auto_mult:
            elapsed = now - last_auto_change_at
            if elapsed >= auto_debounce_sec or last_auto_change_at == 0.0:
                if target != last_auto_mult:
                    logger.info(
                        "rumble_auto_policy_change",
                        mult=target,
                        battery_pct=battery_pct,
                    )
                return target, target, now
            # Dentro do debounce: manter mult anterior.
            return last_auto_mult, last_auto_mult, last_auto_change_at

        return last_auto_mult, last_auto_mult, last_auto_change_at

    # Política desconhecida: fallback para balanceado.
    logger.warning("rumble_policy_desconhecida", policy=policy)
    return 0.7, last_auto_mult, last_auto_change_at


class RumbleEngine:
    """Throttle com política de intensidade (FEAT-RUMBLE-POLICY-01).

    Guarda o último comando pedido; `tick(now)` aplica se o intervalo
    estourou OU se o comando é stop (0,0). Em stop o throttle é ignorado
    para garantir desligamento imediato quando o jogo solta o gatilho.

    A política de rumble é aplicada pelo método `_apply_with_policy` antes
    de enviar ao hardware. Requer `link(config, state_ref)` para funcionar
    em modo não-default.
    """

    def __init__(
        self,
        controller: IController,
        min_interval_sec: float = DEFAULT_MIN_INTERVAL_SEC,
        *,
        time_fn: Callable[[], float] | None = None,
    ) -> None:
        self._controller = controller
        self._min_interval = min_interval_sec
        self._time = time_fn or time.monotonic
        self._pending: RumbleCommand | None = None
        self._last_applied: RumbleCommand | None = None
        self._last_applied_at: float = 0.0
        # Referências injetadas via link() para aplicar política.
        self._config: Any | None = None
        self._state_ref: Any | None = None
        # FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01: referência opcional ao
        # ProfileManager para leitura O(1) do override de policy por perfil.
        self._profile_manager: Any | None = None
        # Debounce do modo "auto".
        self._last_auto_mult: float = 0.7
        self._last_auto_change_at: float = 0.0
        # Último mult efetivo para exposição via IPC (daemon.state_full).
        self._last_mult_applied: float = 1.0

    def link(
        self,
        config: DaemonConfig,
        state_ref: Any,
        *,
        profile_manager: ProfileManager | None = None,
    ) -> None:
        """Injeta referência ao DaemonConfig e ao estado do controle.

        `state_ref` deve ter atributo `battery_pct: int`; pode ser o objeto
        ControllerState mais recente guardado pelo poll loop, ou qualquer
        objeto com duck-typing compatível.

        FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01: `profile_manager` opcional
        permite ao engine consultar `get_active_rumble_config()` a cada tick
        para aplicar override de policy por perfil. Quando None (caminho
        atual em produção sem wire-up), comportamento pré-sprint preservado.
        """
        self._config = config
        self._state_ref = state_ref
        self._profile_manager = profile_manager

    def set(self, weak: int, strong: int) -> None:
        weak = _clamp(weak)
        strong = _clamp(strong)
        self._pending = RumbleCommand(weak=weak, strong=strong)

    def tick(self) -> RumbleCommand | None:
        """Aplica `pending` se tempo permitir. Retorna o comando aplicado ou None."""
        if self._pending is None:
            return None

        now = self._time()
        cmd = self._pending

        if cmd.is_stop():
            return self._apply(cmd, now)

        if self._last_applied is None:
            return self._apply(cmd, now)

        interval = now - self._last_applied_at
        if interval >= self._min_interval:
            return self._apply(cmd, now)
        return None

    def stop(self) -> None:
        """Forçar desligamento imediato dos motores."""
        self.set(0, 0)
        self.tick()

    @property
    def last_applied(self) -> RumbleCommand | None:
        return self._last_applied

    @property
    def last_mult_applied(self) -> float:
        """Último multiplicador efetivo usado (para daemon.state_full)."""
        return self._last_mult_applied

    def update_auto_state(
        self,
        auto_mult: float,
        change_at: float,
        *,
        mult_applied: float | None = None,
    ) -> None:
        """Atualiza o estado de debounce do modo "auto" e o mult efetivo aplicado.

        Encapsula a escrita dos campos privados `_last_auto_mult`,
        `_last_auto_change_at` e `_last_mult_applied`. Usado por chamadores
        externos (ex.: `_apply_rumble_policy` em `ipc_server.py`) que precisam
        propagar o resultado de `_effective_mult` de volta ao engine sem
        tocar atributos privados diretamente.

        Args:
            auto_mult: novo valor do debounce state de auto (último mult alvo
                confirmado pelo debounce). Para policies fixas, é o mesmo
                valor que entrou.
            change_at: timestamp da última mudança de debounce.
            mult_applied: (opcional) mult efetivo aplicado no hardware nesse
                ciclo. Para policy "auto", normalmente == auto_mult. Para
                policies fixas (economia/balanceado/max/custom), difere —
                nesse caso o chamador passa o mult efetivo aqui; se None,
                assume `auto_mult`.

        AUDIT-FINDING-RUMBLE-POLICY-DEDUP-01: substitui writeback direto em
        `rumble_engine._last_auto_*` / `._last_mult_applied` por método público.
        """
        self._last_auto_mult = auto_mult
        self._last_auto_change_at = change_at
        self._last_mult_applied = mult_applied if mult_applied is not None else auto_mult

    def _compute_mult(self, now: float) -> float:
        """Calcula multiplicador atual conforme política do config."""
        if self._config is None:
            return 1.0
        battery_pct = 50  # fallback neutro se estado indisponível
        if self._state_ref is not None:
            with contextlib.suppress(AttributeError, TypeError, ValueError):
                battery_pct = int(self._state_ref.battery_pct)

        # FEAT-RUMBLE-PER-PROFILE-OVERRIDE-01: lê override do perfil ativo (se
        # ProfileManager foi linkado). Consulta O(1), sem hit de disco.
        profile_override: RumbleConfig | None = None
        if self._profile_manager is not None:
            with contextlib.suppress(AttributeError):
                profile_override = self._profile_manager.get_active_rumble_config()

        mult, self._last_auto_mult, self._last_auto_change_at = _effective_mult(
            config=self._config,
            battery_pct=battery_pct,
            now=now,
            last_auto_mult=self._last_auto_mult,
            last_auto_change_at=self._last_auto_change_at,
            profile_override=profile_override,
        )
        return mult

    def _apply(self, cmd: RumbleCommand, now: float) -> RumbleCommand:
        mult = self._compute_mult(now)
        self._last_mult_applied = mult
        effective_weak = _clamp(round(cmd.weak * mult))
        effective_strong = _clamp(round(cmd.strong * mult))
        self._controller.set_rumble(weak=effective_weak, strong=effective_strong)
        self._last_applied = cmd
        self._last_applied_at = now
        self._pending = None
        return cmd

    @property
    def mult_applied(self) -> float:
        """Alias de last_mult_applied — conveniente para testes."""
        return self._last_mult_applied


def _clamp(value: int) -> int:
    if value < RUMBLE_MIN:
        return RUMBLE_MIN
    if value > RUMBLE_MAX:
        return RUMBLE_MAX
    return value


__all__ = [
    "DEFAULT_MIN_INTERVAL_SEC",
    "RUMBLE_MAX",
    "RUMBLE_MIN",
    "RumbleCommand",
    "RumbleEngine",
    "_effective_mult",
]
