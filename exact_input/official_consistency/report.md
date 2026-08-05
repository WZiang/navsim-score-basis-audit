# official-environment consistency diagnostic Exact-Input Environment Consistency Gate

- direct-solve accuracy gate: `FAIL`
- max direct-solve pairwise absolute vector difference: `0.000e+00`
- max direct-solve pairwise relative vector difference: `0.000e+00`
- exact-input diagnostic relative residual: `9.318e-04`
- feedback-closure diagnostic relative residual: `1.890e-16`
- exact-input diagnostic/feedback-closure diagnostic residual absolute difference: `9.318e-04`

| Source | relative residual | backward error | forward error | v0 (m/s) |
|---|---:|---:|---:|---:|
| exact-input diagnostic historical | 9.317783e-04 | n/a | n/a | 12.535506708 |
| feedback-closure diagnostic historical | 1.889789e-16 | n/a | n/a | 12.533835468 |
| official-environment consistency diagnostic run1 | 9.317783e-04 | 4.369766e-04 | 4.932286e-01 | 12.535506708 |
| official-environment consistency diagnostic run2 | 9.317783e-04 | 4.369766e-04 | 4.932286e-01 | 12.535506708 |
| official-environment consistency diagnostic run3 | 9.317783e-04 | 4.369766e-04 | 4.932286e-01 | 12.535506708 |

## Gate Checks

- all_backward_error_le_1e-12: `False`
- all_forward_error_le_1e-11: `False`
- all_relative_residual_le_1e-12: `False`
- default_pinv_failed: `True`
- environment_gate_passed: `True`
- hermitian_and_lstsq_normal: `True`
- input_gate_passed: `True`
- thread_gate_passed: `True`
- three_runs_present: `True`
- vector_max_absolute_pairwise_difference_le_1e-12: `True`
- vector_max_relative_pairwise_difference_le_1e-12: `True`

## Decision

The direct-solve accuracy gate fails reproducibly in all three official-environment processes. We therefore use the official-environment consistency diagnostic values for numerical reporting and classify direct solve only as a non-divergent behavioral control, not an accuracy anchor. The exact-input diagnostic/feedback-closure diagnostic discrepancy is retained as runtime-specific provenance; we do not attribute an internal implementation cause.

official-environment consistency diagnostic uses three independent official-environment processes with the same canonical NPZ and fixed single-thread settings. It does not run NAVSIM scorer or read the dataset.
