# FEAT-FLATPAK-BUNDLE-01 — Versão Flatpak do Hefesto

**Tipo:** feat (packaging).
**Wave:** V1.1 ou V1.2.
**Estimativa:** 2 iterações.
**Dependências:** FEAT-COSMIC-WAYLAND-01 (Flatpak é o meio canônico de distribuir em COSMIC).

---

## Contexto

Usuário solicitou versão Flatpak para uso em Pop!_OS COSMIC. Flatpak é o formato de pacote preferido no COSMIC Store. Desafios específicos do Hefesto:

1. **Acesso a `/dev/hidraw*`**: sandbox padrão do Flatpak bloqueia. Necessita `--device=all` ou permissão `--device=input` (pode não bastar para hidraw).
2. **Acesso a `/dev/uinput`**: idem, para emulação de mouse/gamepad.
3. **D-Bus system**: daemon systemd user fora do sandbox. Alternativa: rodar daemon DENTRO do Flatpak via `--socket=session-bus`.
4. **udev rules**: não podem ser instaladas pelo Flatpak. Usuário precisa instalar uma vez via `flatpak run --command=sh br.andrefarias.Hefesto -c 'install-host-udev.sh'` ou receber instrução clara no README.
5. **python-xlib + GTK3 + PyGObject**: runtime do Flatpak `org.gnome.Platform//45` inclui quase tudo; só pydualsense + evdev via `pip install --target`.

## Decisão

Criar `br.andrefarias.Hefesto.yml` (manifest Flatpak) com:

```yaml
app-id: br.andrefarias.Hefesto
runtime: org.gnome.Platform
runtime-version: "45"
sdk: org.gnome.Sdk
command: hefesto-gui

finish-args:
  - --share=ipc
  - --socket=fallback-x11
  - --socket=wayland
  - --socket=session-bus
  - --device=all          # necessário para hidraw + uinput
  - --filesystem=xdg-run/hefesto:create
  - --filesystem=xdg-config/hefesto:create
  - --filesystem=host-os:ro  # pra ler /sys/bus/usb se precisar
  - --talk-name=org.freedesktop.portal.*
  - --own-name=org.freedesktop.systemd1.ManagedObject  # opcional

modules:
  - name: hefesto
    buildsystem: simple
    build-commands:
      - pip3 install --prefix=/app --no-deps ./dist/*.whl
      - install -Dm644 assets/appimage/Hefesto.png /app/share/icons/hicolor/256x256/apps/br.andrefarias.Hefesto.png
      - install -Dm644 assets/hefesto.desktop /app/share/applications/br.andrefarias.Hefesto.desktop
    sources:
      - type: dir
        path: .
```

## Critérios de aceite

- [ ] `flatpak/br.andrefarias.Hefesto.yml` (manifest).
- [ ] `flatpak/br.andrefarias.Hefesto.metainfo.xml` (AppStream metadata com screenshot, descrição PT-BR/EN, oars).
- [ ] `scripts/build_flatpak.sh`: script local `flatpak-builder --user --install-deps-from=flathub --install --force-clean build-dir flatpak/*.yml`.
- [ ] `scripts/install-host-udev.sh` (dentro do bundle Flatpak): copia as 3 rules do `/app/share/hefesto/udev-rules/` para `/etc/udev/rules.d/` via `pkexec` (polkit).
- [ ] Workflow `.github/workflows/flatpak.yml` (opcional inicial): build flatpak em CI, upload artifact.
- [ ] Documentação em `docs/usage/flatpak.md`: como instalar, como rodar udev, limitações.
- [ ] Smoke: `flatpak run br.andrefarias.Hefesto` abre a GUI; daemon roda dentro do sandbox; conecta em DualSense plugado.

## Arquivos tocados (previsão)

- `flatpak/br.andrefarias.Hefesto.yml`
- `flatpak/br.andrefarias.Hefesto.metainfo.xml`
- `scripts/build_flatpak.sh`
- `scripts/install-host-udev.sh`
- `.github/workflows/flatpak.yml` (opcional)
- `docs/usage/flatpak.md`

## Fora de escopo

- Submeter ao Flathub (processo separado com revisão humana).
- Publicar no COSMIC Store (depende de pipeline próprio do System76).
- Assinar com OSTree (futuro).

## Notas

- `--device=all` é generoso; tentar `--device=input` primeiro e confirmar se hidraw passa. Se não, cair pra `all`.
- `finish-args` determina permissões no Flatpak — erros aqui quebram o app silenciosamente. Testar com `flatpak run --verbose`.
- Daemon systemd user NÃO roda dentro do Flatpak; a versão Flatpak roda o daemon como processo filho do `hefesto-gui` (sem `--install-service`). Alternativa: portal de background via `org.freedesktop.portal.Background` para manter daemon vivo com janela fechada.
- Perfis em `~/.var/app/br.andrefarias.Hefesto/config/hefesto/` (isolamento Flatpak) — documentar caminho no README.
