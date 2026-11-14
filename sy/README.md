# sy — 150-day gold 1-minute data (three sources)

Archive of 1-minute bars used for the CapitalBomb (炸弹） indicator tests, 2026-11-14.
Saved for future use. The 150-day files supersede the 90-day files
(overlap verified: 0 inconsistencies).

## Files

| File | Bars | Range (UTC) | Source |
|---|---|---|---|
| jrjr_m1_150d.json | 147,347 | 2026-06-17 10:06 → 2026-11-13 21:49 | Jinrong China (金荣） GOLD 1m, decrypted app API |
| comex_m1_150d.json | 150,000 | 2026-06-15 10:21 → 2026-11-13 21:59 | COMEX GC main contract (MI), Pancubic gateway WPCCACHE |
| shfe_m1_150d.json | 55,620 | 2026-06-16 01:00 → 2026-11-13 18:29 | SHFE gold main contract (沪金主连）, Pancubic gateway CCACHE |

## Format

Each file is a JSON array of bars: `[ts, open, high, low, close, vol, pos]`

- `ts`: epoch seconds (UTC)
- `open/high/low/close`: price (Jinrong and COMEX in USD/oz; SHFE in CNY/g)
- `vol`: volume for the minute (Jinrong = lots on Jinrong platform; COMEX = contracts; SHFE = contracts)
- `pos`: open interest (position quantity; Jinrong file carries it where available)

## Notes

- SHFE main-contract rollovers inside the window: 2026-07-27 au2608 → au2610,
  2026-09-24 → 2026-09-28 au2610 → au2612 (current main contract au2612).
  Do not treat the first 60 minutes after a rollover as bomb signals
  (known false trigger: rollover first bar z ≈ 59).
- Jinrong was pulled in two 75-day segments (single 150-day window returns HTTP 502);
  overlap 725 bars, 0 inconsistencies.
- COMEX was pulled in 75 pages x 2000 bars; SHFE covers 103 trading days
  (SHFE trades ~555 minutes/day).
- Files are 2.8–8.7 MB each, over GitHub's 1 MB Contents API limit:
  fetch them via raw.githubusercontent.com, not the Contents API.
