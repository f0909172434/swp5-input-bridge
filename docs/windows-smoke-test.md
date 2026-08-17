# Windows / SWP 5.5 smoke test

Do this once before using the bridge on an important document.

1. Open Scientific WorkPlace 5.5 and create a disposable blank document.
2. Put the cursor in an empty body paragraph.
3. Run `swp5-input doctor`.
4. Run each `plan` command and inspect the action list.
5. Run the matching `write` command only in the disposable document.

## Test 1: subscript and limit

```powershell
swp5-input plan  --expr "\lim_{\rho\to0^+}K_\rho(m_\rho)=0"
swp5-input write --expr "\lim_{\rho\to0^+}K_\rho(m_\rho)=0" --yes
```

Expected visual result: a real SWP mathematics object representing the limit expression, not pasted LaTeX source.

## Test 2: fraction

```powershell
swp5-input write --expr "\frac{1}{2}" --yes
```

Expected visual result: a fraction template with 1 over 2.

## Test 3: integral

```powershell
swp5-input write --expr "F(s)=\int_0^s f(t)dt" --yes
```

Expected visual result: an integral with lower limit 0 and upper limit s.

If any test fails, stop. Do not use the bridge on the research manuscript. Open an issue with a screenshot and the output from `swp5-input plan ...`.
