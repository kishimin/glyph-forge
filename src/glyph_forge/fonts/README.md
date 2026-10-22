# Bundled fonts

- `ipaexg.ttf`: existing IPAex Gothic font for Latin letters, digits, and Japanese.
- `NotoEmoji.ttf`: unmodified monochrome Noto Emoji variable font, downloaded from
  [Google Fonts](https://github.com/google/fonts/tree/8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5/ofl/notoemoji).
  The upstream filename is `NotoEmoji[wght].ttf`. Its SIL Open Font License 1.1
  and copyright notice are included in `NotoEmoji-OFL.txt` and distributed with
  the package.

Emoji use the configured text color. Font selection occurs per grapheme, so
ordinary letters and Japanese text retain the existing font. Emoji coverage
depends on this bundled font version. Combined sequences such as ZWJ emoji and
flags require Pillow's Raqm layout support for composition; without it, Pillow
may display their components together within one cell. The production container
installs `libfribidi0` to enable Raqm in the Linux Pillow wheel. Local environments
need the corresponding FriBiDi library; verify availability with
`python -c "from PIL import features; print(features.check_feature('raqm'))"`.
