from pathlib import Path
import argparse
import json

import pandas as pd


MODEL_DIR = Path(__file__).resolve().parents[1]
FUTURE_OUTPUT = (
    MODEL_DIR / "outputs" / "future" / "future_projection_by_mineral.csv"
)
OUTPUT_DIR = MODEL_DIR / "outputs" / "sensitivity"

MIN_ADJUSTMENT_PCT = -10
MAX_ADJUSTMENT_PCT = 10
STEP_PCT = 1


def load_future_output():
    detail = pd.read_csv(FUTURE_OUTPUT)

    required_columns = {
        "mineral_id",
        "mineral_name",
        "year",
        "scenario",
        "energy_demand_mwh",
    }

    missing = required_columns - set(detail.columns)

    if missing:
        raise ValueError(f"Colunas ausentes no output futuro: {missing}")

    if detail["energy_demand_mwh"].isna().any():
        raise ValueError("Há energia ausente no output futuro.")

    return detail


def validate_adjustments(raw_adjustments, mineral_ids):
    adjustments = {mineral_id: 0 for mineral_id in mineral_ids}

    for mineral_id, value in raw_adjustments.items():
        if mineral_id not in adjustments:
            raise ValueError(f"Mineral desconhecido: {mineral_id}")

        if not isinstance(value, (int, float)):
            raise ValueError(f"Ajuste inválido para {mineral_id}")

        if value < MIN_ADJUSTMENT_PCT or value > MAX_ADJUSTMENT_PCT:
            raise ValueError(
                f"Ajuste de {mineral_id} fora do intervalo permitido."
            )

        if float(value) != int(value):
            raise ValueError(
                f"O ajuste de {mineral_id} deve usar intervalos de 1%."
            )

        adjustments[mineral_id] = int(value)

    return adjustments


def calculate_custom_result(base, adjustments):
    result = base.copy()

    result["adjustment_pct"] = result["mineral_id"].map(adjustments)
    result["adjusted_energy_mwh"] = (
        result["energy_demand_mwh"]
        * (1 + result["adjustment_pct"] / 100)
    )

    return result


def build_global_range(detail):
    rows = []

    for (scenario, year), base in detail.groupby(["scenario", "year"]):
        base_total = base["energy_demand_mwh"].sum()

        for adjustment_pct in range(
            MIN_ADJUSTMENT_PCT,
            MAX_ADJUSTMENT_PCT + 1,
            STEP_PCT,
        ):
            rows.append(
                {
                    "scenario": scenario,
                    "year": int(year),
                    "global_adjustment_pct": adjustment_pct,
                    "total_energy_demand_mwh": (
                        base_total * (1 + adjustment_pct / 100)
                    ),
                    "method": "all_intensities_adjusted_equally",
                }
            )

    return pd.DataFrame(rows)


def build_one_way_sensitivity(detail):
    rows = []

    for (scenario, year), base in detail.groupby(["scenario", "year"]):
        base_total = base["energy_demand_mwh"].sum()

        for _, mineral in base.iterrows():
            for adjustment_pct in range(
                MIN_ADJUSTMENT_PCT,
                MAX_ADJUSTMENT_PCT + 1,
                STEP_PCT,
            ):
                adjusted_total = (
                    base_total
                    + mineral["energy_demand_mwh"] * adjustment_pct / 100
                )

                rows.append(
                    {
                        "scenario": scenario,
                        "year": int(year),
                        "varied_mineral_id": mineral["mineral_id"],
                        "varied_mineral_name": mineral["mineral_name"],
                        "adjustment_pct": adjustment_pct,
                        "total_energy_demand_mwh": adjusted_total,
                        "difference_from_base_mwh": (
                            adjusted_total - base_total
                        ),
                        "method": "one_intensity_adjusted_others_fixed",
                    }
                )

    return pd.DataFrame(rows)


def build_contract(detail):
    base_energy = detail[
        [
            "scenario",
            "year",
            "mineral_id",
            "mineral_name",
            "production_basis",
            "energy_demand_mwh",
        ]
    ].copy()

    base_energy = base_energy.rename(
        columns={"energy_demand_mwh": "base_energy_mwh"}
    )

    return {
        "version": "1.0.0",
        "purpose": (
            "Interactive sensitivity analysis for energy-intensity "
            "benchmark assumptions."
        ),
        "allowed_adjustment_pct": {
            "minimum": MIN_ADJUSTMENT_PCT,
            "maximum": MAX_ADJUSTMENT_PCT,
            "step": STEP_PCT,
        },
        "formula": (
            "adjusted_energy_mwh = base_energy_mwh * "
            "(1 + adjustment_pct / 100)"
        ),
        "total_formula": (
            "total_adjusted_energy_mwh = sum(adjusted_energy_mwh)"
        ),
        "base_energy_by_mineral": base_energy.to_dict(orient="records"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="referencia")
    parser.add_argument("--year", type=int, default=2040)
    parser.add_argument(
        "--adjustments",
        default="{}",
        help='JSON, ex.: {"MIN_011": 3, "MIN_022": -5}',
    )
    args = parser.parse_args()

    detail = load_future_output()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    global_range = build_global_range(detail)
    one_way = build_one_way_sensitivity(detail)
    contract = build_contract(detail)

    global_range.to_csv(
        OUTPUT_DIR / "intensity_global_range.csv",
        index=False,
        encoding="utf-8-sig",
    )

    one_way.to_csv(
        OUTPUT_DIR / "intensity_one_way.csv",
        index=False,
        encoding="utf-8-sig",
    )

    with open(
        OUTPUT_DIR / "intensity_sensitivity_contract.json",
        "w",
        encoding="utf-8",
    ) as output_file:
        json.dump(contract, output_file, ensure_ascii=False, indent=2)

    base = detail[
        (detail["scenario"] == args.scenario)
        & (detail["year"] == args.year)
    ].copy()

    if base.empty:
        raise ValueError("Cenário ou ano não disponível.")

    raw_adjustments = json.loads(args.adjustments)
    adjustments = validate_adjustments(
        raw_adjustments,
        base["mineral_id"].tolist(),
    )

    custom_result = calculate_custom_result(base, adjustments)

    custom_output = {
        "scenario": args.scenario,
        "year": args.year,
        "adjustments_pct": adjustments,
        "total_base_energy_mwh": float(
            custom_result["energy_demand_mwh"].sum()
        ),
        "total_adjusted_energy_mwh": float(
            custom_result["adjusted_energy_mwh"].sum()
        ),
        "by_mineral": custom_result[
            [
                "mineral_id",
                "mineral_name",
                "energy_demand_mwh",
                "adjustment_pct",
                "adjusted_energy_mwh",
            ]
        ].to_dict(orient="records"),
    }

    with open(
        OUTPUT_DIR / "custom_intensity_result.json",
        "w",
        encoding="utf-8",
    ) as output_file:
        json.dump(custom_output, output_file, ensure_ascii=False, indent=2)

    print(json.dumps(custom_output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
