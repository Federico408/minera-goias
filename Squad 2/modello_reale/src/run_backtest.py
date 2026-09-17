from pathlib import Path

import pandas as pd

from common import load_historical_production


MODEL_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = MODEL_DIR / "outputs" / "backtest"


def calculate_annual_growth_rate(history):
    first = history.iloc[0]
    last = history.iloc[-1]

    years = int(last["year"]) - int(first["year"])

    if years <= 0 or first["production_t"] <= 0:
        raise ValueError("Série histórica inválida para calcular tendência.")

    return (last["production_t"] / first["production_t"]) ** (1 / years) - 1


def run_backtest():
    history = load_historical_production()
    results = []

    for mineral_id, mineral_history in history.groupby("mineral_id"):
        mineral_history = mineral_history.sort_values("year").reset_index(drop=True)

        # Os dois últimos anos são ocultados ao modelo.
        test = mineral_history.tail(2)
        train = mineral_history.iloc[:-2]

        if len(train) < 4:
            raise ValueError(
                f"Série insuficiente para backtest: {mineral_id}"
            )

        growth_rate = calculate_annual_growth_rate(train)
        base = train.iloc[-1]

        for _, actual in test.iterrows():
            years_after_base = int(actual["year"]) - int(base["year"])
            forecast = base["production_t"] * (1 + growth_rate) ** years_after_base
            absolute_error = abs(forecast - actual["production_t"])
            absolute_percentage_error = absolute_error / actual["production_t"]

            results.append(
                {
                    "mineral_id": mineral_id,
                    "mineral_name": actual["mineral_name"],
                    "production_basis": actual["production_basis"],
                    "train_through_year": int(base["year"]),
                    "test_year": int(actual["year"]),
                    "actual_production_t": actual["production_t"],
                    "forecast_production_t": forecast,
                    "annual_growth_rate_used": growth_rate,
                    "absolute_error_t": absolute_error,
                    "absolute_percentage_error": absolute_percentage_error,
                    "method": "historical_compound_growth_rate",
                }
            )

    detail = pd.DataFrame(results)

    if detail.empty or detail.isna().any().any():
        raise ValueError("Backtest gerou resultados ausentes.")

    summary = (
        detail.groupby(
            ["mineral_id", "mineral_name", "production_basis"],
            as_index=False,
        )
        .agg(
            tested_years=("test_year", "count"),
            mean_absolute_percentage_error=(
                "absolute_percentage_error",
                "mean",
            ),
        )
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    detail.to_csv(
        OUTPUT_DIR / "backtest_detail.csv",
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        OUTPUT_DIR / "backtest_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print(summary.to_string(index=False))


if __name__ == "__main__":
    run_backtest()
