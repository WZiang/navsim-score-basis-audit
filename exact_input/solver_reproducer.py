from __future__ import annotations

import json
from pathlib import Path

import numpy as np

SANITY_V0_THRESHOLD = 100.0
SANITY_ACCEL_THRESHOLD = 20.0


def backward_error(normal: np.ndarray, rhs: np.ndarray, x: np.ndarray) -> float:
    residual = np.linalg.norm(normal @ x - rhs)
    return float(residual / (np.linalg.norm(normal, 2) * np.linalg.norm(x) + np.linalg.norm(rhs)))


def solve_all(normal: np.ndarray, rhs: np.ndarray) -> list[dict[str, float | bool | str]]:
    solvers = {
        "np_pinv_default": lambda n, r: np.linalg.pinv(n) @ r,
        "np_pinv_hermitian": lambda n, r: np.linalg.pinv(n, hermitian=True) @ r,
        "np_solve": lambda n, r: np.linalg.solve(n, r),
        "np_lstsq": lambda n, r: np.linalg.lstsq(n, r, rcond=None)[0],
    }
    rows = []
    for name, fn in solvers.items():
        x = np.asarray(fn(normal, rhs), dtype=np.float64)
        v0 = float(x[0])
        accel = x[1:]
        max_a = float(np.max(np.abs(accel))) if accel.size else 0.0
        rows.append(
            {
                "solver": name,
                "v0_mps": v0,
                "max_abs_velocity": float(np.max(np.abs(x))),
                "max_abs_acceleration": max_a,
                "normal_residual_l2": float(np.linalg.norm(normal @ x - rhs)),
                "backward_error": backward_error(normal, rhs, x),
                "within_fitted_state_sanity_bounds": bool(
                    abs(v0) < SANITY_V0_THRESHOLD and max_a < SANITY_ACCEL_THRESHOLD
                ),
            }
        )
    return rows


def main() -> None:
    here = Path(__file__).resolve().parent
    npz_path = here / "canonical_input.npz"
    with np.load(npz_path) as data:
        normal = np.asarray(data["normal"], dtype=np.float64)
        rhs = np.asarray(data["rhs"], dtype=np.float64)
    rows = solve_all(normal, rhs)
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
