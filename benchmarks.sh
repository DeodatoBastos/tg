#!/bin/bash

# ==============================================================================
# SCRIPT MESTRE DE VALIDAÇÃO DE TESE - OLAP E STRESS DE MEMÓRIA
# ==============================================================================

set -e
export SCALE=100

echo "🚀 INICIANDO TESTE MESTRE PARA OS 3 CENÁRIOS (SCALE: $SCALE) 🚀"

# Função de limpeza absoluta e segura para Podman/Docker Compose
cleanup() {
    echo "🧹 Limpando todos os contêineres..."
    # Usar down explicitamente nas pastas para garantir que o compose mate a rede e as portas
    (cd /home/deodato/ita/CSC27/tg/postgre && docker compose down -v >/dev/null 2>&1 || true)
    (cd /home/deodato/ita/CSC27/tg/citus && docker compose down -v >/dev/null 2>&1 || true)
    (cd /home/deodato/ita/CSC27/tg/citus && docker compose -f docker-compose-patroni.yml down -v >/dev/null 2>&1 || true)
    
    # Tiro de misericórdia para garantir
    docker rm -f $(docker ps -aq) >/dev/null 2>&1 || true
    docker volume prune -f >/dev/null 2>&1 || true
}

echo -e "\n\n========================================================="
echo "📊 INICIANDO CENÁRIO 1: MONOLÍTICO"
echo "========================================================="
cleanup
cd /home/deodato/ita/CSC27/tg/postgre
echo "⏳ Subindo contêineres..."
docker compose up -d
echo "⏳ Aguardando banco iniciar..."
sleep 15
echo "🔥 Rodando Benchmark (Monolítico)..."
./benchmark_universal.sh
echo "✅ Cenário 1 concluído."

echo -e "\n\n========================================================="
echo "📊 INICIANDO CENÁRIO 2: CITUS SIMPLES"
echo "========================================================="
cleanup
cd /home/deodato/ita/CSC27/tg/citus
echo "⏳ Subindo contêineres..."
docker compose up -d
echo "⏳ Aguardando cluster e coordenador..."
sleep 20
echo "🔥 Rodando Benchmark (Citus Simples)..."
./benchmark_universal.sh citus
echo "✅ Cenário 2 concluído."

echo -e "\n\n========================================================="
echo "📊 INICIANDO CENÁRIO 3: CITUS PATRONI (HA)"
echo "========================================================="
cleanup
cd /home/deodato/ita/CSC27/tg/citus
echo "⏳ Subindo contêineres Patroni..."
docker compose -f docker-compose-patroni.yml up -d
echo "⏳ Aguardando Eleição do Patroni..."
sleep 45
echo "🔥 Rodando Benchmark (Citus Patroni)..."
./benchmark_universal.sh citus patroni
echo "✅ Cenário 3 concluído."

cleanup
echo -e "\n\n🎉🎉 TODOS OS TESTES FORAM CONCLUÍDOS COM SUCESSO! 🎉🎉"
