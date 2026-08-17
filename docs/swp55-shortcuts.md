# Scientific WorkPlace 5.5 keyboard profile

The v0.1 live driver is keyboard-first. Its default profile uses documented SWP 5.5 shortcuts:

| Object | Shortcut used by the driver |
|---|---|
| Start mathematics | `Ctrl+M` |
| Return to text | `Ctrl+T` |
| Display mathematics | `Ctrl+D` |
| Fraction | `Ctrl+F` |
| Radical | `Ctrl+R` |
| Superscript | `Ctrl+H` |
| Subscript | `Ctrl+L` |
| Integral | `Ctrl+I` |
| Next template field | `Tab` |
| Leave a template | `Space` |
| Leave a display | `Right Arrow` |

SWP 5.5 also accepts many TeX-named symbols by holding `Ctrl` while typing the TeX name. The bridge uses this for symbols such as `rho`, `lambda`, `infty`, `to`, and `lim`.

## Sources

The defaults were checked against the Scientific WorkPlace 5.5 *Creating Documents* manual and Scientific Word Ltd.'s v5.5 support material. Before broad use, run the three smoke tests in `docs/windows-smoke-test.md` on the target SWP installation.

## Why there is a calibration step

SWP 5.5 is legacy Windows software. Keyboard behavior can be changed in user settings, and local installations may differ. The bridge therefore treats the documented shortcuts as defaults rather than assuming every installation is identical.
