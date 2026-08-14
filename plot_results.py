import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    sns.set_theme(style="whitegrid")
    
    # Caminhos para os relatórios mais recentes (diretórios gerados pelos links simbólicos do script bash)
    paths = [
        "postgre/latest_results_postgresql/reports/benchmark_results.csv",
        "citus/latest_results_citus/reports/benchmark_results.csv",
        "citus/latest_results_citus_patroni/reports/benchmark_results.csv"
    ]
    
    data = []
    for p in paths:
        if os.path.exists(p):
            print(f"Lendo {p}...")
            df = pd.read_csv(p)
            data.append(df)
        else:
            print(f"AVISO: Arquivo não encontrado: {p}")
            
    if not data:
        print("Nenhum arquivo CSV encontrado. Execute os benchmarks primeiro.")
        sys.exit(1)
        
    df_all = pd.concat(data, ignore_index=True)
    
    # Agregar pela média das execuções ("Run" column)
    df_agg = df_all.groupby(["Database_Type", "Clients"]).agg({
        "TPS": "mean",
        "Latency_Avg_ms": "mean"
    }).reset_index()
    
    # Configurar cores bonitas
    palette = sns.color_palette("husl", len(df_agg['Database_Type'].unique()))
    
    # 1. Gráfico de TPS
    plt.figure(figsize=(10, 6))
    sns.lineplot(
        data=df_agg, 
        x="Clients", 
        y="TPS", 
        hue="Database_Type", 
        marker="o", 
        linewidth=2.5,
        markersize=8,
        palette=palette
    )
    plt.title("Comparação de Desempenho (TPS)", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Número de Clientes Simultâneos", fontsize=12)
    plt.ylabel("Transações por Segundo (TPS)", fontsize=12)
    plt.xticks(df_agg['Clients'].unique())
    plt.legend(title="Arquitetura", title_fontsize='13', fontsize='11')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig("tps_comparative_plot.png", dpi=300, bbox_inches='tight')
    print("✅ Gráfico gerado: tps_comparative_plot.png")
    
    # 2. Gráfico de Latência
    plt.figure(figsize=(10, 6))
    sns.lineplot(
        data=df_agg, 
        x="Clients", 
        y="Latency_Avg_ms", 
        hue="Database_Type", 
        marker="s", 
        linewidth=2.5,
        markersize=8,
        palette=palette
    )
    plt.title("Comparação de Latência Média", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Número de Clientes Simultâneos", fontsize=12)
    plt.ylabel("Latência Média (ms)", fontsize=12)
    plt.xticks(df_agg['Clients'].unique())
    plt.legend(title="Arquitetura", title_fontsize='13', fontsize='11')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig("latency_comparative_plot.png", dpi=300, bbox_inches='tight')
    print("✅ Gráfico gerado: latency_comparative_plot.png")

if __name__ == "__main__":
    main()
