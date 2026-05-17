# BUG-FLATPAK-LOCALE-SYMLINK-01

**Status:** MERGED (v3.4.1, 2026-05-17)
**Tipo:** BUG
**Tamanho:** S (1 commit, ~30 linhas trocadas em 2 arquivos)
**Origem:** validação manual pós-release v3.4.0 (usuária)

## Contexto

A release v3.4.0 introduziu o pipeline i18n EN baseline com `po/en.po` +
`po/pt_BR.po` (identidade) bundlados em 5 destinos. Validação manual no
Flatpak pós-deploy mostrou que **somente o catálogo `en.mo`** chegava ao
app; o `pt_BR.mo` aparecia ausente.

Reprodução:

```bash
flatpak install --user -y dist/flatpak/hefesto-dualsense4unix-3.4.0.flatpak
flatpak run --command=find br.andrefarias.Hefesto /app/share/locale/ -name "hefesto*"
# Output: /app/share/locale/en/LC_MESSAGES/hefesto-dualsense4unix.mo  (só EN)

flatpak run --command=stat br.andrefarias.Hefesto /app/share/locale/pt_BR
# Output:
#   Arquivo: /app/share/locale/pt_BR -> ../../share/runtime/locale/pt/share/pt_BR
#   modo: symbolic link
```

O entry `pt_BR` no `/app/share/locale/` é um **symlink injetado pela
Locale Extension** do runtime `org.gnome.Platform//47`, apontando para
`/app/share/runtime/locale/pt/share/pt_BR` (read-only, pertence ao
runtime). Nosso `install -Dm644` no manifest do flatpak-builder rodava
**antes do deploy**, mas o deployer do Flatpak materializava o symlink
sobre nosso diretório real depois.

Curiosamente, `en` não tinha symlink correspondente porque o runtime
GNOME 47 não traz traduções EN built-in (assume EN como default sem
catálogo). Só `pt_BR` (e provavelmente `de`, `es`, `fr`, `zh_CN`, etc.)
sofria essa intercepção.

## Decisão

Instalar nossos catálogos em **path próprio do app** que o runtime
nunca toca, e ensinar o `utils/i18n.py` a procurar nesse path antes do
`/app/share/locale/` canônico.

Path escolhido: `/app/share/hefesto-dualsense4unix/locale/<lang>/LC_MESSAGES/<dom>.mo`.

Alternativas consideradas e rejeitadas:

| Alternativa | Por que não |
|---|---|
| `rm -f /app/share/locale/<lang>` antes do install | Symlink é recriado pelo deployer depois do build; rm no manifest é no-op no app final |
| Declarar nosso app como Locale Extension via `add-extensions:` | Complexidade excessiva para 2 idiomas; mecanismo é desenhado para distribuir locale-packs separados |
| Override do candidate path `/app/share/locale/` via env var custom | Quebra integração com `LANG`/`LC_MESSAGES` standard; usuários esperam comportamento gettext nativo |

## Implementação

**`flatpak/br.andrefarias.Hefesto.yml`** — módulo `hefesto`,
`build-commands`:

```yaml
- |
  if [ -d locale ]; then
    for lang_dir in locale/*/; do
      [ -d "$lang_dir" ] || continue
      lang="$(basename "$lang_dir")"
      mo="${lang_dir}LC_MESSAGES/hefesto-dualsense4unix.mo"
      target_dir="/app/share/hefesto-dualsense4unix/locale/${lang}/LC_MESSAGES"
      if [ -f "$mo" ]; then
        install -Dm644 "$mo" "${target_dir}/hefesto-dualsense4unix.mo"
      fi
    done
  fi
```

**`src/hefesto_dualsense4unix/utils/i18n.py`** —
`_candidate_locale_dirs()`:

```python
# 4a. /app/share/hefesto-dualsense4unix/locale/ (Flatpak sandbox —
#     path proprio porque /app/share/locale/<lang> e sobrescrito por
#     symlinks da Locale Extension do runtime GNOME//47).
candidates.append(Path("/app/share/hefesto-dualsense4unix/locale"))

# 4b. /app/share/locale/ (Flatpak fallback caso o app instale em
#     path canonico — mantido como fallback defensivo).
candidates.append(Path("/app/share/locale"))
```

Demais candidate paths (`$XDG_DATA_HOME/locale`, `~/.local/share/locale`,
`/usr/share/locale`, wheel `pkg_locale`) permanecem inalterados.

## Validation

```bash
# Build + instala
PATH="$PWD/.venv/bin:$PATH" bash scripts/build_flatpak.sh --bundle
mkdir -p dist/flatpak && mv -f br.andrefarias.Hefesto.flatpak \
    dist/flatpak/hefesto-dualsense4unix-3.4.1.flatpak
flatpak install --user -y --reinstall \
    dist/flatpak/hefesto-dualsense4unix-3.4.1.flatpak

# Confirma .mo no path próprio
flatpak run --command=find br.andrefarias.Hefesto \
    /app/share/hefesto-dualsense4unix/locale/ -name "*.mo"
# Output:
#   /app/share/hefesto-dualsense4unix/locale/en/LC_MESSAGES/hefesto-dualsense4unix.mo
#   /app/share/hefesto-dualsense4unix/locale/pt_BR/LC_MESSAGES/hefesto-dualsense4unix.mo

# Smoke EN
flatpak run --env=LANG=en_US.UTF-8 --env=LANGUAGE=en \
    --command=python3 br.andrefarias.Hefesto -c "
from hefesto_dualsense4unix.utils.i18n import _, init_locale
init_locale()
print(_('Aplicar'), _('Sair'))"
# Output:
#   i18n_initialized domain=hefesto-dualsense4unix locale=en_US
#       locale_dir=/app/share/hefesto-dualsense4unix/locale
#   Apply Quit

# Smoke PT-BR identity
flatpak run --env=LANG=pt_BR.UTF-8 --command=python3 br.andrefarias.Hefesto -c "
from hefesto_dualsense4unix.utils.i18n import _, init_locale
init_locale()
print(_('Aplicar') == 'Aplicar')"
# Output:
#   i18n_initialized ... locale=pt_BR locale_dir=/app/share/hefesto-dualsense4unix/locale
#   True
```

## Critérios de aceite

- [x] `/app/share/hefesto-dualsense4unix/locale/{en,pt_BR}/LC_MESSAGES/hefesto-dualsense4unix.mo` presentes.
- [x] `--env=LANG=en_US.UTF-8 --env=LANGUAGE=en` resolve traduções EN.
- [x] `--env=LANG=pt_BR.UTF-8` mantém PT-BR (identity).
- [x] `.deb`, AppImage, wheel continuam funcionando (candidate paths 2/3/5 inalterados).
- [x] Suite 1415+ passed mantida.
- [x] Bump v3.4.0 → v3.4.1 em pyproject + __init__ + control + flatpak metainfo + README + CHANGELOG.

## Lições aprendidas

1. **Flatpak runtime extensions são opacas no build time**: o
   `flatpak-builder` cria o app em `/app/` sem materializar
   extensions; estas vêm no deploy. Validar SEMPRE pós-deploy, não no
   build sandbox.
2. **Validação manual encontrou o que CI não pegaria**: o smoke CI da
   v3.4.0 (validação automatizada de `flatpak run version` + i18n EN)
   passava porque EN funcionava. PT-BR identity precisa de teste
   explícito anti-fallback (verificar `locale_dir` no log + msgstr
   identity).
3. **GitHub release imutabilidade vs hotfix**: optar por v3.4.1 patch
   preserva v3.4.0 como artifact verificável. `gh release upload
   --clobber` seria mais barato mas degrada confiança em tags.

## Refs

- Manifest: `flatpak/br.andrefarias.Hefesto.yml` (módulo `hefesto`)
- Implementação: `src/hefesto_dualsense4unix/utils/i18n.py` (linhas 66-74)
- Sprint pai: `FEAT-I18N-CATALOGS-01` (MERGED v3.4.0)
- Release: <https://github.com/[REDACTED]/hefesto-dualsense4unix/releases/tag/v3.4.1>
- Validação por usuária: triagem 2026-05-17 (Pop!_OS COSMIC + Flatpak local install)
