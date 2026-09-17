from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]

SQUAD1_INTERFACE = (
    ROOT
    / "Squad 1"
    / "Bases consolidadas"
    / "documentacao"
    / "pacote_squad2"
    / "interface_squad1_squad2.csv"
)

SQUAD1_WORKBOOK = (
    ROOT
    / "Squad 1"
    / "Bases consolidadas"
    / "documentacao"
    / "prototipo_bases_consolidadas_v17.xlsx"
)

MODEL_DIR = Path(__file__).resolve().parents[1]
ENERGY_PARAMETERS = MODEL_DIR / "parameters" / "energy_intensity.csv"
SCENARIO_PARAMETERS = MODEL_DIR / "parameters" / "scenarios.csv"


def load_parameters():
    energy = pd.read_csv(ENERGY_PARAMETERS)
    scenarios = pd.read_csv(SCENARIO_PARAMETERS)

    if energy.duplicated(["mineral_id", "production_basis"]).any():
        raise ValueError("Há parâmetros energéticos duplicados.")

    if set(scenarios["scenario"]) != {
        "conservador",
        "referencia",
        "expansao",
    }:
        raise ValueError("Os três cenários obrigatórios não estão completos.")

    return energy, scenarios


def load_historical_production():
    energy, _ = load_parameters()

    # Quatro minerais disponíveis diretamente na interface Squad 1 → Squad 2.
    interface = pd.read_csv(SQUAD1_INTERFACE)
    direct = interface[
        (interface["nivel_agregacao"] == "estado")
        & (interface["valor_observado_estimado"] == "observado")
    ].copy()

    direct["production_basis"] = direct["production_basis"].str.lower()

    direct = direct.merge(
        energy[
            energy["mineral_name"].isin(
                ["Alumínio (Bauxita)", "Níquel", "Fosfato", "Amianto"]
            )
        ][["mineral_id", "mineral_name", "production_basis"]],
        on=["mineral_id", "mineral_name", "production_basis"],
        how="inner",
    )

    direct = direct[
        [
            "mineral_id",
            "mineral_name",
            "year",
            "production_t",
            "production_basis",
            "source_id",
            "status_validacao",
            "periodo_referencia",
        ]
    ]

    # Il rame usa contenuto minerale: questa misura è nella base completa
    # della Squad 1, non ancora nel CSV di interfaccia.
    full_data = pd.read_excel(
        SQUAD1_WORKBOOK,
        sheet_name="08_fato_producao_energia",
        header=3,
    )

    copper = full_data[
        (full_data["uf"] == "GO")
        & (full_data["mineral_name"] == "Cobre")
        & (full_data["metrica"] == "contido_beneficiada")
        & (full_data["production_basis"] == "conteudo_mineral")
        & (full_data["unidade_padrao"] == "t")
        & (full_data["status_validacao"] == "valido")
    ].copy()

    copper = copper.rename(columns={"valor_tratado": "production_t"})[
        [
            "mineral_id",
            "mineral_name",
            "year",
            "production_t",
            "production_basis",
            "source_id",
            "status_validacao",
            "periodo_referencia",
        ]
    ]

    history = pd.concat([direct, copper], ignore_index=True)
    history = history.sort_values(["mineral_id", "year"])

    if history.duplicated(
        ["mineral_id", "year", "production_basis"]
    ).any():
        raise ValueError("Há observações históricas duplicadas.")

    if history["production_t"].isna().any() or (history["production_t"] < 0).any():
        raise ValueError("Há produção ausente ou negativa.")

    return history


if __name__ == "__main__":
    history = load_historical_production()

    print(
        history.groupby(
            ["mineral_name", "production_basis"]
        ).agg(
            primeiro_ano=("year", "min"),
            ultimo_ano=("year", "max"),
            observacoes=("year", "size"),
        )
    )
