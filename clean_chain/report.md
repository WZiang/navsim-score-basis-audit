# feedback-closure diagnostic Clean 32-Token Mechanism Smoke

- selection status: `deterministic_failure_reproduction_smoke`
- token manifest sha256: `51a005dfe299844f25a840b04b2d54dd27ad81429bfd35b0df421ffde31c0840`
- parent pool recovered: `False`
- tokens are sorted: `True`
- subset of E47 stage1 pool: `False`
- summarize started: `2026-07-15T07:24:32.253084Z`
- summarize ended: `2026-07-15T07:24:32.256300Z`
- verdict branch: `scoped_mechanism_chain`

| Setting | div. IA | div. Human | ref core fail | overwrite IA(any-core) | Ignore-All | Human | margin |
|---|---:|---:|---:|---:|---:|---:|---:|
| B filter-on | 1.000 | 1.000 | 1.000 | 1.000 | 0.8571 | 0.7712 | 0.0859 |
| B filter-off | 1.000 | 1.000 | 1.000 | 0.000 | 0.0000 | 0.0000 | 0.0000 |
| B2 filter-on | 0.000 | 0.000 | 0.156 | 0.125 | 0.1250 | 0.9901 | -0.8651 |

## Material Completeness

- `smoke32_selection.json` records the frozen token-manifest hash and the unrecovered-selection limitation.
- `clean_chain_per_token.csv` is fully traceable to per-token environment/setting/agent rows.
- `clean_chain_summary.csv` aggregates any-core overwrite across DAC/DDC/LK rather than DAC alone.
- `scoped_mechanism_chain` means the deterministic smoke reproduces the expected B failure, filter-off collapse, and B2 ranking reversal; it does not estimate prevalence because the parent-pool selection rule was not recovered.
- B2 may retain localized any-core overwrite; the gate tests its reduction relative to B and the corresponding ranking reversal, not an artificial requirement of exactly zero overwrite.
- `command_log.ndjson` records the feedback-closure diagnostic clean-chain subcommands with input/output hashes and timestamps.
