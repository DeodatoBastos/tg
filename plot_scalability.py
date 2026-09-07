#!/usr/bin/env python3
"""Gera curva de escalabilidade: TPS e Latência vs Clientes Simultâneos.

Uso:
    python3 plot_scalability.py

Lê os CSVs gerados por benchmark_scalability.sh e produz dois gráficos:
1. TPS vs Concorrência (quanto maior, melhor)
2. Latência vs Concorrência (quanto menor, melhor)
"""
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scalability_results")

LABEL_MAP = {
    "postgre": "PostgreSQL (Monolito — 2 CPUs)",
    "citus": "Citus (Distribuído — 6 CPUs)",
}

COLORS = {
    "PostgreSQL (Monolito — 2 CPUs)": "#66c2a5",
    "Citus (Distribuído — 6 CPUs)": "#fc8d62",
}


def load_results() -> pd.DataFrame:
    """Carrega e combina CSVs de todos os tipos de banco."""
    frames = []
    for csv_name in ["postgre_scalability.csv", "citus_scalability.csv"]:
        csv_path = os.path.join(RESULTS_DIR, csv_name)
        if not os.path.exists(csv_path):
            print(f"AVISO: {csv_path} não encontrado, pulando.")
            continue
        df = pd.read_csv(csv_path)
        frames.append(df)

    if not frames:
        print("Nenhum CSV encontrado. Execute benchmark_scalability.sh primeiro.")
        sys.exit(1)

    combined = pd.concat(frames, ignore_index=True)
    # Remover runs que falharam (tps=0)
    combined = combined[combined["tps"] > 0]
    # Label legível
    combined["Arquitetura"] = combined["db_type"].map(LABEL_MAP)
    return combined


def plot_tps_curve(df: pd.DataFrame) -> None:
    """Gráfico de linha: TPS médio por nível de concorrência."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 7))

    sns.lineplot(
        data=df,
        x="clients",
        y="tps",
        hue="Arquitetura",
        style="Arquitetura",
        markers=True,
        dashes=False,
        markersize=10,
        linewidth=2.5,
        palette=COLORS,
        errorbar="sd",
        ax=ax,
    )

    ax.set_title(
        "Curva de Escalabilidade — Throughput (TPS)",
        fontsize=16, fontweight="bold", pad=20,
    )
    ax.set_xlabel("Clientes Simultâneos", fontsize=13)
    ax.set_ylabel("Transações por Segundo (TPS)", fontsize=13)
    ax.set_xticks(sorted(df["clients"].unique()))
    ax.legend(title="Arquitetura", fontsize=11, title_fontsize=12)

    # Anotação da zona de saturação
    ax.axvspan(64, 260, alpha=0.08, color="red", label="Zona de saturação do Monolito")
    ax.text(
        160, ax.get_ylim()[1] * 0.95,
        "← Zona de saturação",
        fontsize=10, color="red", alpha=0.7, ha="center",
    )

    plt.tight_layout()
    out = os.path.join(os.path.dirname(RESULTS_DIR), "scalability_tps.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    print(f"✅ Gráfico salvo: {out}")
    plt.close()


def plot_latency_curve(df: pd.DataFrame) -> None:
    """Gráfico de linha: Latência média por nível de concorrência."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 7))

    sns.lineplot(
        data=df,
        x="clients",
        y="latency_avg_ms",
        hue="Arquitetura",
        style="Arquitetura",
        markers=True,
        dashes=False,
        markersize=10,
        linewidth=2.5,
        palette=COLORS,
        errorbar="sd",
        ax=ax,
    )

    ax.set_title(
        "Curva de Escalabilidade — Latência Média",
        fontsize=16, fontweight="bold", pad=20,
    )
    ax.set_xlabel("Clientes Simultâneos", fontsize=13)
    ax.set_ylabel("Latência Média (ms)", fontsize=13)
    ax.set_xticks(sorted(df["clients"].unique()))
    ax.legend(title="Arquitetura", fontsize=11, title_fontsize=12)

    plt.tight_layout()
    out = os.path.join(os.path.dirname(RESULTS_DIR), "scalability_latency.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    print(f"✅ Gráfico salvo: {out}")
    plt.close()


def main() -> None:
    df = load_results()
    print(f"Total de medições: {len(df)}")
    print(df.groupby(["db_type", "clients"])["tps"].agg(["mean", "std"]).to_string())
    print()
    plot_tps_curve(df)
    plot_latency_curve(df)


if __name__ == "__main__":
    main()
