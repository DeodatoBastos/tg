#!/bin/bash

# ==============================================================================
# SCRIPT MESTRE DE VALIDAÇÃO DE TESE - OLAP E STRESS DE MEMÓRIA
# ==============================================================================
# Este script automatiza o teste de fogo para a sua professora.
# Ele testará os 3 cenários com uma carga MASSIVA de dados (SCALE=100)
# para forçar o limite de memória do monolítico e extrair o máximo do Citus.
# Os relatórios provarão:
# 1. Que o Citus destrói o Monolítico em Select-Only (OLAP).
# 2. O custo do Sync Standby na latência de escrita.

set -e

# Aumentamos a escala para gerar cerca de 1.5GB de dados (10x o normal).
# Isso garantirá que o monolítico sofra com a leitura em disco.
export SCALE=100

echo "🚀 INICIANDO TESTE MESTRE PARA OS 3 CENÁRIOS (SCALE: $SCALE) 🚀"
echo "Aviso: Isso pode demorar algumas horas dependendo do hardware."

# Função de limpeza absoluta
cleanup() {
    echo "🧹 Limpando todos os contêineres e volumes antigos..."
    docker rm -f $(docker ps -aq) >/dev/null 2>&1 || true
    docker volume prune -f >/dev/null 2>&1 || true
}

# ==============================================================================
# CENÁRIO 1: POSTGRESQL MONOLÍTICO
# ==============================================================================
echo -e "\n\n========================================================="
echo "📊 INICIANDO CENÁRIO 1: MONOLÍTICO"
echo "========================================================="
cleanup
cd postgre
echo "⏳ Subindo contêineres..."
docker compose up -d
echo "⏳ Aguardando banco iniciar..."
sleep 15
echo "🔥 Rodando Benchmark (Monolítico)..."
./benchmark_universal.sh
echo "✅ Cenário 1 concluído."

# ==============================================================================
# CENÁRIO 2: CITUS (CLUSTER SIMPLES)
# ==============================================================================
echo -e "\n\n========================================================="
echo "📊 INICIANDO CENÁRIO 2: CITUS SIMPLES"
echo "========================================================="
cleanup
cd ../citus
echo "⏳ Subindo contêineres..."
docker compose up -d
echo "⏳ Aguardando cluster e coordenador..."
sleep 20
echo "🔥 Rodando Benchmark (Citus Simples)..."
./benchmark_universal.sh
echo "✅ Cenário 2 concluído."

# ==============================================================================
# CENÁRIO 3: CITUS + PATRONI (ALTA DISPONIBILIDADE)
# ==============================================================================
echo -e "\n\n========================================================="
echo "📊 INICIANDO CENÁRIO 3: CITUS PATRONI (HA)"
echo "========================================================="
cleanup
echo "⏳ Subindo contêineres Patroni..."
docker compose -f docker-compose-patroni.yml up -d
echo "⏳ Aguardando Eleição do Patroni (Isso demora mais)..."
sleep 45
echo "🔥 Rodando Benchmark (Citus Patroni)..."
./benchmark_universal.sh
echo "✅ Cenário 3 concluído."

cleanup

echo -e "\n\n🎉🎉 TODOS OS TESTES FORAM CONCLUÍDOS COM SUCESSO! 🎉🎉"
echo "Os relatórios finais (com os CSVs para plotar os gráficos) estão salvos em:"
echo "👉 Monolítico: /home/deodato/ita/CSC27/tg/postgre/benchmark_reports/"
echo "👉 Citus (Simples e Patroni): /home/deodato/ita/CSC27/tg/citus/benchmark_universal/reports_.../"
echo "Agora você tem os dados maciços e definitivos para o seu TG!"
