from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text())


def read_rows(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(newline="") as handle:
        return list(csv.DictReader(handle))


def token_count(relative: str) -> int:
    value = load_json(relative)
    tokens = value.get("tokens", value) if isinstance(value, dict) else value
    return len(tokens)


def close(actual: float, expected: float, rel: float = 1e-9, abs_: float = 1e-12) -> None:
    if not math.isclose(float(actual), float(expected), rel_tol=rel, abs_tol=abs_):
        raise AssertionError(f"{actual} != {expected}")


def valid_scores(relative: str) -> dict[str, float]:
    scores: dict[str, float] = {}
    for row in read_rows(relative):
        token = row["token"].strip()
        if token == "aggregate_summary_row" or row["valid"].strip().lower() != "true":
            continue
        score = float(row["score"])
        if not math.isfinite(score):
            continue
        if token in scores:
            raise AssertionError(f"{relative}: duplicate token {token}")
        scores[token] = score
    return scores


def mean_score(relative: str, expected_n: int) -> float:
    scores = valid_scores(relative)
    assert len(scores) == expected_n, (relative, len(scores), expected_n)
    return sum(scores.values()) / len(scores)


def check_scopes() -> None:
    assert token_count("token_lists/full_navtest_tokens.json") == 12146
    assert token_count("token_lists/matched_intersection_tokens_12143.json") == 12143
    assert token_count("token_lists/control_pool_stage1_tokens.json") == 450
    assert token_count("token_lists/smoke32_tokens.json") == 32


def check_matched_consequence() -> None:
    matched = set(load_json("token_lists/matched_intersection_tokens_12143.json"))
    summary = {
        (row["basis"], row["agent"]): row
        for row in read_rows("score_files/matched_scope/matched_intersection_scores.csv")
    }
    expected_ranks = {
        "stock_filter_on": ["ignore_all", "human_replay", "diffusion_drive", "pdm_closed", "lead_release"],
        "two_sided": ["human_replay", "pdm_closed", "diffusion_drive", "lead_release", "ignore_all"],
        "fallback": ["human_replay", "pdm_closed", "diffusion_drive", "lead_release", "ignore_all"],
    }
    for (basis, agent), expected in summary.items():
        relative = f"score_files/matched_scope/per_token/{basis}__{agent}.csv"
        scores = valid_scores(relative)
        assert set(scores) == matched and len(scores) == 12143
        assert int(expected["matched_n"]) == 12143
        close(sum(scores.values()) / len(scores) * 100.0, expected["mean_epdms_x100"], abs_=5e-5)
    for basis, expected in expected_ranks.items():
        ranked = sorted(
            (agent for row_basis, agent in summary if row_basis == basis),
            key=lambda agent: float(summary[(basis, agent)]["mean_epdms_x100"]),
            reverse=True,
        )
        assert ranked == expected, (basis, ranked)


def check_full_navtest_and_controls() -> None:
    expected = {
        "score_files/full_navtest/ignore_all_stock_reactive.csv": (12146, 0.7963585895415304),
        "score_files/full_navtest/human_replay_stock_reactive.csv": (12146, 0.7398820305332737),
        "score_files/full_navtest/pdm_closed_stock_reactive.csv": (12146, 0.6712712225528249),
        "score_files/full_navtest/actor_blind_stock_reactive.csv": (12146, 0.7924537178612596),
        "score_files/full_navtest/human_replay_two_sided_reactive.csv": (12146, 0.8891228152713415),
        "score_files/full_navtest/pdm_closed_two_sided_reactive.csv": (12146, 0.8624267836559949),
        "score_files/full_navtest/ignore_all_two_sided_reactive.csv": (12146, 0.13288472395380016),
        "score_files/full_navtest/actor_blind_two_sided_reactive.csv": (12146, 0.4507686245912822),
        "score_files/full_navtest/human_replay_fallback_reactive.csv": (12146, 0.8834338004260673),
        "score_files/full_navtest/pdm_closed_fallback_reactive.csv": (12146, 0.8596530663759132),
        "score_files/full_navtest/ignore_all_fallback_reactive.csv": (12146, 0.13281652448181336),
        "score_files/full_navtest/actor_blind_fallback_reactive.csv": (12146, 0.4507190723852097),
        "score_files/full_navtest/human_replay_filter_off_reactive.csv": (12146, 0.0),
        "score_files/full_navtest/pdm_closed_filter_off_reactive.csv": (12146, 0.000896576346809699),
        "score_files/full_navtest/ignore_all_filter_off_reactive.csv": (12146, 0.0),
    }
    for relative, (count, score) in expected.items():
        close(mean_score(relative, count), score)
    nonreactive_ignore = mean_score("score_files/full_navtest/ignore_all_stock_nonreactive.csv", 12146)
    nonreactive_human = mean_score("score_files/full_navtest/human_replay_stock_nonreactive.csv", 12146)
    close((nonreactive_ignore - nonreactive_human) * 100.0, 5.91493966267556)

    bootstrap = load_json("bootstrap/cluster_bootstrap_summary.json")
    expected_bootstrap = {
        "route_aware_minus_human_stock": (5.257168732798569, 4.369871103422286, 6.172312991377602),
        "route_aware_minus_pdm_stock": (12.118249530843448, 10.527788350635664, 13.728539697614412),
        "route_aware_minus_ignoreall_stock": (-0.3904871680270988, -0.9339382389313685, 0.18424561826214292),
        "ignoreall_minus_human_stock": (5.647655900825668, 4.787122056614205, 6.577209373647401),
        "ignoreall_minus_human_twosided": (-75.62380913175413, -78.01419733356336, -73.20302925407145),
        "ignoreall_minus_human_fallback": (-75.06172759442539, -77.56474692958953, -72.61871395173758),
    }
    for name, (point, low, high) in expected_bootstrap.items():
        row = bootstrap[name]
        assert row["n_tokens"] == 12146 and row["n_logs"] == 136
        close(row["point"], point)
        close(row["ci_low"], low)
        close(row["ci_high"], high)


def check_score_basis_and_robustness() -> None:
    disclosure = load_json("score_basis/score_basis_stability_summary.json")
    rows = {row["agent"]: row for row in disclosure["rows"]}
    expected = {
        "ignore_all": (0.7963585895415304, 0.0, 0.13288472395380016, 0.13281652448181336, 1.0, 68.35093295259475, 195.49291285951574),
        "human_replay": (0.7398820305332737, 0.0, 0.8891228152713415, 0.8834338004260673, 0.9944014490367199, 7.216640745387122, 22.751548350141693),
        "pdm_closed": (0.6712712225528249, 0.000896576346809699, 0.8624267836559949, 0.8596530663759132, 0.9947307755639717, 4.223019294256473, 12.486507349756616),
        "diffusiondrive": (0.7371442688909542, 0.0, 0.8528340843048906, 0.8488118080669967, 0.9960471053281726, 7.075056333368936, 21.921236843002912),
    }
    for agent, values in expected.items():
        row = rows[agent]
        for field, value in zip(("filter_on_score", "filter_off_score", "two_sided_score", "e32a_score", "e32a_fallback_rate", "median_path_dev_km", "p90_path_dev_km"), values):
            close(row[field], value)

    lifts = {
        (row["agent"], row["traffic"], row["metric"]): row
        for row in read_rows("score_basis/metric_lift_summary.csv")
    }
    expected_rates = {
        "drivable_area_compliance": 0.9998353367363741,
        "driving_direction_compliance": 0.9998353367363741,
        "lane_keeping": 0.9991766836818706,
        "time_to_collision_within_bound": 0.02634612218014161,
        "no_at_fault_collisions": 0.023876173225753333,
    }
    for metric, expected_rate in expected_rates.items():
        close(lifts[("ignore_all", "reactive", metric)]["fail_to_pass_rate"], expected_rate)

    thresholds = read_rows("robustness/fallback_threshold_sensitivity.csv")
    assert {row["threshold"] for row in thresholds} == {"strict", "mid", "current", "loose"}
    for row in thresholds:
        assert int(row["blind_rank"]) == 4
        assert float(row["blind_minus_human_ci_high"]) < 0
        assert float(row["blind_minus_pdm_closed_ci_high"]) < 0


def check_negative_controls() -> None:
    rows = read_rows("negative_controls/open_loop_lead574_per_token.csv")
    by_agent: dict[str, list[float]] = {}
    for row in rows:
        by_agent.setdefault(row["agent"], []).append(float(row["ADE"]))
    means = {agent: sum(values) / len(values) for agent, values in by_agent.items()}
    assert set(means) == {"human_replay", "lead_release", "constant_velocity", "timid_creep", "ignore_all"}
    assert all(len(values) == 574 for values in by_agent.values())
    close(means["ignore_all"], 7.627519373566581)
    close(means["lead_release"], 0.5422083794334964)
    assert max(means, key=means.get) == "ignore_all"

    submetrics = read_rows("negative_controls/submetric_reweighting_reactive.csv")
    assert len(submetrics) == 8
    max_margin = max(float(row["delta_pdmclosed"]) for row in submetrics)
    close(max_margin, 0.17)


def check_clean_chain() -> None:
    rows = {(r["environment"], r["setting"]): r for r in read_rows("clean_chain/clean_chain_summary.csv")}
    assert set(rows) == {("B", "filter_on"), ("B", "filter_off"), ("B2", "filter_on")}
    b_on, b_off, b2 = rows[("B", "filter_on")], rows[("B", "filter_off")], rows[("B2", "filter_on")]
    assert int(b_on["token_count"]) == int(b_off["token_count"]) == int(b2["token_count"]) == 32
    close(b_on["human_ref_core_fail_rate"], 1.0)
    close(b_on["overwrite_rate_ignore_all"], 1.0)
    assert float(b_on["margin_ignore_all_minus_human"]) > 0
    close(b_off["overwrite_rate_ignore_all"], 0.0)
    close(b_off["margin_ignore_all_minus_human"], 0.0)
    close(b2["divergence_rate_ignore_all"], 0.0)
    assert float(b2["margin_ignore_all_minus_human"]) < 0
    selection = load_json("clean_chain/smoke32_selection.json")
    assert selection["selection_status"] == "deterministic_failure_reproduction_smoke"
    assert selection["parent_pool_recovered"] is False


def check_exact_input() -> None:
    hp = load_json("exact_input/high_precision/high_precision_reference.json")
    assert hp["reference_dps"] == 200 and hp["crosscheck_dps"] == 100
    assert float(hp["agreement_100_vs_200"]) < 1e-90
    gate = load_json("exact_input/official_consistency/report.json")
    assert len(gate["direct_solve_runs"]) == 3
    assert gate["max_direct_solve_pairwise_absolute_difference"] == 0.0
    checks = gate["gate_checks"]
    assert checks["input_gate_passed"] and checks["environment_gate_passed"] and checks["thread_gate_passed"]
    assert checks["default_pinv_failed"] and checks["hermitian_and_lstsq_normal"]
    direct = gate["direct_solve_runs"][0]
    close(direct["relative_residual"], 9.317783336184161e-4)
    close(direct["backward_error"], 4.369765602425747e-4)
    close(direct["forward_relative_error"], 4.932285852706178e-1)
    run = load_json("exact_input/official_consistency/run1.json")["results"]
    close(run["np_pinv_default"]["v0_mps"], -491.34368772026994)
    close(run["np_pinv_default"]["max_abs_acceleration"], 305752.7639572796)
    close(run["np_pinv_default"]["relative_residual"], 836.3274738768195)
    assert run["np_pinv_hermitian"]["forward_relative_error"] < 4e-13
    assert run["np_lstsq"]["forward_relative_error"] < 1e-13
    rows = read_rows("exact_input/high_precision/solver_accuracy.csv")
    b2_default = next(row for row in rows if row["environment"] == "B2" and row["solver"] == "np_pinv_default")
    close(b2_default["relative_residual"], 4.2016222155815994e-14)


def check_route_tail() -> None:
    report = load_json("route/route_tail_sensitivity.json")
    metrics = report["route_metrics"]
    assert metrics["n_valid"] == 12146 and metrics["n_tail"] == 118
    close(metrics["p99_max_lateral_m"], 3.7548912551549805)
    close(metrics["max_max_lateral_m"], 44.81857095775908)
    full = report["route_aware_minus_human_stock_points"]["all_valid"]
    trimmed = report["route_aware_minus_human_stock_points"]["excluding_route_tail"]
    assert full["n_tokens"] == 12146 and trimmed["n_tokens"] == 12028
    assert full["n_logs"] == trimmed["n_logs"] == 136
    assert full["draws"] == trimmed["draws"] == 4000
    assert full["seed"] == trimmed["seed"] == 0
    close(full["ci_low"], 4.369871103422284)
    close(full["ci_high"], 6.172312991377602)
    close(trimmed["ci_low"], 4.408905851854482)
    close(trimmed["ci_high"], 6.217791353230467)


def check_route_tail_causal_trace() -> None:
    rows = read_rows("route/causal_trace_per_token.csv")
    traced_tokens = {row["token"] for row in rows}
    tail_tokens = {row["token"] for row in read_rows("route/route_tail_tokens.csv")}
    assert len(rows) == len(traced_tokens) == len(tail_tokens) == 118
    assert traced_tokens == tail_tokens
    assert all(row["route_tail_ge_4m"].lower() == "true" for row in rows)
    assert all(row["route_builder_stop_reason"] == "no_outgoing_edge" for row in rows)
    assert all(row["endpoint_extrapolation_used"].lower() == "true" for row in rows)
    summary = load_json("route/causal_trace_summary.json")
    assert summary["n_tail"] == 118
    assert summary["baseline_reproduction_passed"]
    assert summary["instrumentation_reproduction_passed"]
    assert summary["trace_reproduction_passed"]
    assert summary["route_builder_stop_reason_counts"] == {"no_outgoing_edge": 118}
    assert summary["endpoint_extrapolation_used_true"] == 118


def check_actor_visibility() -> None:
    rows = read_rows("visibility/paired_collision_control.csv")
    assert len(rows) == len({row["token"] for row in rows}) == 10
    assert all(row["straight_valid"].lower() == "true" for row in rows)
    assert all(row["stopped_valid"].lower() == "true" for row in rows)
    assert sum(float(row["straight_nc"]) == 1.0 for row in rows) == 2
    assert all(float(row["stopped_nc"]) == 1.0 for row in rows)
    assert all(float(row["stopped_ttc"]) == 1.0 for row in rows)
    actor_counts = [int(row["n_actors"]) for row in rows]
    assert min(actor_counts) == 63 and max(actor_counts) == 272
    summary = load_json("visibility/paired_collision_control_summary.json")
    assert summary == {
        "n_paired_collision_risk_tokens": 10,
        "n_straight_collision_success": 2,
        "n_stopped_collision_success": 10,
        "n_collision_success_recoveries": 8,
        "n_stopped_ttc_success": 10,
        "actor_count_min": 63,
        "actor_count_max": 272,
    }


def main() -> None:
    check_scopes()
    check_matched_consequence()
    check_full_navtest_and_controls()
    check_score_basis_and_robustness()
    check_negative_controls()
    check_clean_chain()
    check_exact_input()
    check_route_tail()
    check_route_tail_causal_trace()
    check_actor_visibility()
    print("PASS: scopes, main tables, robustness controls, clean-chain, exact-input, route-tail, and visibility checks")


if __name__ == "__main__":
    main()
