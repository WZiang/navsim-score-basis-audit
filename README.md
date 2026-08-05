# When Shared Rollouts Fail in Defensive-Driving Evaluation

Reproducibility artifact for "When Shared Rollouts Fail in Defensive-Driving
Evaluation: A NAVSIM Score-Basis Audit," by Ziang Wei, Minjun Yu, Zheyuan Lai,
Mingjie Pang, and Wei Li from EABOT.AI.

This release provides the frozen per-token scores, token lists, exact-input arrays,
offline recomputation tools, and provenance used for the paper's audit. It verifies the
reported full-navtest ranking, diagnostic reversals, robustness controls, mechanism
smoke test, and numerical checks without requiring NAVSIM.

It is an audit artifact over committed NAVSIM outputs, not a planner-training release.
The NAVSIM dataset, third-party checkpoints, and planner training code are not included.

## Quick Start

The claim verifier requires only Python 3. The optional recomputation scripts require
Python 3, NumPy, and pandas:

```bash
pip install -r requirements.txt
python verify_claims.py
python bootstrap/recompute_offline_metrics.py --output-dir /tmp/navsim-audit-recomputed
python exact_input/solver_reproducer.py
sha256sum -c MANIFEST.sha256
```

`verify_claims.py` checks the reported values and scope constraints. The recomputation
script regenerates the clustered bootstrap, route-token summary, and exact-input errors
from frozen local inputs. The solver reproducer evaluates the 40x40 numerical diagnostic.

## Data Scope

- 12,146 tokens: full-navtest fixed-policy/reference audit and route sensitivity.
- 12,143 tokens: matched published-agent consequence audit.
- 450 tokens: frozen stage-one solver/control pool.
- 32 tokens: deterministic mechanism smoke only.
- One 40x40 system: exact-input numerical diagnostic only.

The 32-token smoke test demonstrates a scoped mechanism chain; it is not a
prevalence estimate.

## Repository Layout

- `score_files/` and `token_lists/`: frozen inputs for the score-basis audit.
- `bootstrap/`, `route/`, `visibility/`, and `clean_chain/`: offline controls and summaries.
- `exact_input/`: numerical diagnostic inputs, references, and standalone reproducer.
- `provenance/`: environment records and source manifests.

`MANIFEST.sha256` verifies the frozen artifact files. Environment records under
`provenance/` document the original runs and are not expected to validate a new local
environment byte-for-byte.
