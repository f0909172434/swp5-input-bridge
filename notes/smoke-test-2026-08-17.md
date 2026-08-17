# SWP 5.5 live smoke-test notes — 2026-08-17

Observed on the user's Scientific WorkPlace 5.5 installation:

- lowercase TeX names such as `\rho`, `\lim`, and `\to` work when Ctrl is held continuously across the command name;
- display math and subscripts/superscripts work;
- `\Lambda` currently renders as lowercase `\lambda` because the driver does not preserve the uppercase first letter while Ctrl is held.

The next driver patch must send the first letter of capital TeX command names with Shift held, while keeping Ctrl depressed for the complete name.
