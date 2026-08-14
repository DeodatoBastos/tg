import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    sns.set_theme(style="whitegrid")
    
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
    
    # Substituir os valores para os nomes mais legíveis nas legendas
    df_all['Database_Type'] = df_all['Database_Type'].replace({
        'postgresql': 'PostgreSQL (Monolito)',
        'citus': 'Citus (Distribuído Simples)',
        'citus_patroni': 'Citus + Patroni (HA)'
    })
    
    palette = sns.color_palette("Set2", len(df_all['Database_Type'].unique()))
    suites = df_all['Suite'].unique()
    
    for suite in suites:
        df_suite = df_all[df_all['Suite'] == suite]
        
        # 1. Gráfico de TPS
        plt.figure(figsize=(10, 6))
        # Passando dados crus, o seaborn barplot calcula média e desenha barra de erro (desvio padrão)
        sns.barplot(
            data=df_suite, 
            x="Clients", 
            y="TPS", 
            hue="Database_Type", 
            palette=palette,
            errorbar='sd',
            capsize=.05
        )
        plt.title(f"Desempenho TPS - Cenário: {suite.upper()}", fontsize=16, fontweight='bold', pad=20)
        plt.xlabel("Número de Clientes Simultâneos", fontsize=12)
        plt.ylabel("Transações por Segundo (TPS)", fontsize=12)
        
        # Posição da legenda ajustada para não cobrir as barras
        plt.legend(title="Arquitetura", title_fontsize='13', fontsize='11', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f"tps_comparative_plot_{suite}.png", dpi=300, bbox_inches='tight')
        print(f"✅ Gráfico gerado: tps_comparative_plot_{suite}.png")
        plt.close()
        
        # 2. Gráfico de Latência
        plt.figure(figsize=(10, 6))
        sns.barplot(
            data=df_suite, 
            x="Clients", 
            y="Latency_Avg_ms", 
            hue="Database_Type", 
            palette=palette,
            errorbar='sd',
            capsize=.05
        )
        plt.title(f"Latência Média - Cenário: {suite.upper()}", fontsize=16, fontweight='bold', pad=20)
        plt.xlabel("Número de Clientes Simultâneos", fontsize=12)
        plt.ylabel("Latência Média (ms)", fontsize=12)
        plt.legend(title="Arquitetura", title_fontsize='13', fontsize='11', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f"latency_comparative_plot_{suite}.png", dpi=300, bbox_inches='tight')
        print(f"✅ Gráfico gerado: latency_comparative_plot_{suite}.png")
        plt.close()

if __name__ == "__main__":
    main()
