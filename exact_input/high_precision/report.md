# Exact-Input High-Precision Diagnostic

## Input Gate

- canonical NPZ: `/ANON_REPO_ROOT/precision_knee_drive/navsim_oracle/results/exact_input_numeric/canonical_input.npz`
- canonical NPZ sha256: `a70959b6833603bd79e08afab588be994e42a1cabe1c1a2c97fbe6edb0dd2d3c`
- normal sha256: `afdced9f8748ff113a564082cc1121d383a7ba5940e1558e075f99560a9a5a9e`
- rhs sha256: `d53960a4e240c5a89d62ef380a39ee6902ef14b3c80dd0b3e51a313caea4021b`
- shape/dtype/rank: `(40, 40)`, `float64`, rank `40`
- exact symmetry: `True`

## High-Precision Reference

- `mpmath` agreement (100 vs 200 dps): `4.165e-99`
- reference relative residual: `0.000e+00`
- reference `v0`: `12.533835468246` m/s

## Solver Verdict

- B default `pinv`: forward error `8.145e+04`, residual `3.495e+03`, backward error `4.211e-02`; role `failed_solver_path`.
- B Hermitian `pinv`: forward error `3.852e-13`, residual `6.991e-15`; role `accuracy_anchor`.
- B direct `solve`: forward error `6.951e-14`, residual `1.890e-16`, backward error `9.360e-17`; role `runtime_specific_cross_check_not_final_anchor`.
- B `lstsq`: forward error `7.044e-14`, residual `1.082e-15`; role `cross_check`.
- B2 default `pinv`: forward error `4.577e-13`, residual `4.202e-14`; role `accuracy_anchor`.

## Material Completeness

- summarize started: `2026-07-15T08:19:30.543955Z`
- summarize ended: `2026-07-15T08:19:30.595610Z`
- Canonical NPZ and metadata are present and hash-matched against exact-input diagnostic anchors.
- Official and NumPy-2 solver vectors are re-solved from the same frozen `(A,b)` rather than inferred from legacy summaries.
- `solver_accuracy.csv` and `pinv_consistency.csv` are regenerated from saved full vectors and the original canonical input.
- A direct-solve result from this runtime is recorded as a runtime-specific cross-check, not a final numerical anchor; official-environment consistency diagnostic is the controlling official-environment consistency gate.
- `command_log.ndjson` records the feedback-closure diagnostic high-precision subcommands with input/output hashes and timestamps.
