from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_TOKENS = {"aggregate_summary_row"}


def load_score(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame = frame[~frame["token"].isin(SUMMARY_TOKENS)].copy()
    keep = ["token", "score", "valid"] + (["log_name"] if "log_name" in frame.columns else [])
    return frame[keep]


def paired_cluster_bootstrap(a: pd.DataFrame, b: pd.DataFrame, draws: int, seed: int) -> dict[str, float | int]:
    merged = a.merge(b, on=["token", "log_name"], how="inner", suffixes=("_a", "_b"))
    merged = merged[merged["valid_a"].astype(bool) & merged["valid_b"].astype(bool)].copy()
    merged["margin"] = (merged["score_a"] - merged["score_b"]) * 100.0
    logs = merged["log_name"].drop_duplicates().to_numpy()
    values = {name: group["margin"].to_numpy() for name, group in merged.groupby("log_name", sort=False)}
    rng = np.random.default_rng(seed)
    samples = np.empty(draws, dtype=np.float64)
    for index in range(draws):
        sampled_logs = rng.choice(logs, size=len(logs), replace=True)
        numerator = sum(float(values[name].sum()) for name in sampled_logs)
        denominator = sum(len(values[name]) for name in sampled_logs)
        samples[index] = numerator / denominator
    low, high = np.percentile(samples, [2.5, 97.5])
    return {
        "point": float(merged["margin"].mean()),
        "ci_low": float(low),
        "ci_high": float(high),
        "n_tokens": int(len(merged)),
        "n_logs": int(len(logs)),
        "draws": draws,
        "seed": seed,
    }


def load_frames() -> dict[tuple[str, str], pd.DataFrame]:
    matched = ROOT / "score_files/matched_scope/per_token"
    frames = {}
    for basis in ("stock_filter_on", "two_sided", "fallback"):
        for agent in ("human_replay", "pdm_closed", "ignore_all", "diffusion_drive", "lead_release"):
            frames[(agent, basis)] = load_score(matched / f"{basis}__{agent}.csv")
    full = ROOT / "score_files/full_navtest"
    frames[("route_aware_actor_blind", "stock_filter_on")] = load_score(full / "actor_blind_stock_reactive.csv")
    frames[("route_aware_actor_blind", "two_sided")] = load_score(full / "actor_blind_two_sided_reactive.csv")
    frames[("route_aware_actor_blind", "fallback")] = load_score(full / "actor_blind_fallback_reactive.csv")
    log_map = frames[("route_aware_actor_blind", "stock_filter_on")][["token", "log_name"]].drop_duplicates()
    for key, frame in list(frames.items()):
        if "log_name" not in frame.columns:
            frame = frame.merge(log_map, on="token", how="left", validate="many_to_one")
        frames[key] = frame[frame["log_name"].notna()].copy()
    return frames


def recompute_exact_input() -> list[dict[str, float | str]]:
    with np.load(ROOT / "exact_input/canonical_input.npz") as data:
        normal = np.asarray(data["normal"], dtype=np.float64)
        rhs = np.asarray(data["rhs"], dtype=np.float64)
    run = json.loads((ROOT / "exact_input/official_consistency/run1.json").read_text())
    reference = json.loads((ROOT / "exact_input/high_precision/high_precision_reference.json").read_text())
    x_ref = np.asarray([float(value) for value in reference["vector_200dps_decimal"]], dtype=np.float64)
    rows = []
    for name, result in run["results"].items():
        x = np.asarray(result["solution_vector"], dtype=np.float64)
        residual = float(np.linalg.norm(normal @ x - rhs))
        rows.append({
            "solver": name,
            "relative_residual": residual / float(np.linalg.norm(rhs)),
            "backward_error": residual / float(np.linalg.norm(normal, 2) * np.linalg.norm(x) + np.linalg.norm(rhs)),
            "forward_relative_error": float(np.linalg.norm(x - x_ref) / np.linalg.norm(x_ref)),
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("recomputed"))
    parser.add_argument("--draws", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    frames = load_frames()
    specs = [
        ("route_aware_minus_human_stock", ("route_aware_actor_blind", "stock_filter_on"), ("human_replay", "stock_filter_on")),
        ("route_aware_minus_pdm_stock", ("route_aware_actor_blind", "stock_filter_on"), ("pdm_closed", "stock_filter_on")),
        ("route_aware_minus_ignoreall_stock", ("route_aware_actor_blind", "stock_filter_on"), ("ignore_all", "stock_filter_on")),
        ("ignoreall_minus_human_stock", ("ignore_all", "stock_filter_on"), ("human_replay", "stock_filter_on")),
        ("ignoreall_minus_human_twosided", ("ignore_all", "two_sided"), ("human_replay", "two_sided")),
        ("ignoreall_minus_human_fallback", ("ignore_all", "fallback"), ("human_replay", "fallback")),
    ]
    boot = {name: paired_cluster_bootstrap(frames[a], frames[b], args.draws, args.seed) for name, a, b in specs}
    (args.output_dir / "cluster_bootstrap_summary.json").write_text(json.dumps(boot, indent=2, sort_keys=True) + "\n")
    pd.DataFrame([{"comparison": name, **value} for name, value in boot.items()]).to_csv(
        args.output_dir / "cluster_bootstrap_summary.csv", index=False
    )

    route = pd.read_csv(ROOT / "route/route_metrics_per_token.csv")
    route = route[route["valid_trajectory"].astype(bool)].copy()
    max_dev = route["max_lateral_distance_to_route_m"].to_numpy()
    end_dev = route["endpoint_distance_to_route_m"].to_numpy()
    route_summary = {
        "n_tokens": int(len(route)),
        "all_points_within_4m_pct": float((max_dev < 4.0).mean() * 100.0),
        "endpoint_within_4m_pct": float((end_dev < 4.0).mean() * 100.0),
        "median_max_route_deviation_m": float(np.median(max_dev)),
        "p90_max_route_deviation_m": float(np.percentile(max_dev, 90)),
        "p99_max_route_deviation_m": float(np.percentile(max_dev, 99)),
        "max_max_route_deviation_m": float(np.max(max_dev)),
    }
    (args.output_dir / "route_metrics_token_summary.json").write_text(json.dumps(route_summary, indent=2, sort_keys=True) + "\n")
    pd.DataFrame(recompute_exact_input()).to_csv(args.output_dir / "official_consistency_recomputed.csv", index=False)
    print(f"Wrote offline recomputation to {args.output_dir}")


if __name__ == "__main__":
    main()
