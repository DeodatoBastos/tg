# ATIVIDADE DIRIGIDA: Bancos de Dados Relacionais Distribuídos

**Disciplina:** CSC-27 **Professores:** Juliana Bezerra e Celso Hirata **Tema:** Escalabilidade Horizontal e Alta Disponibilidade com PostgreSQL, Citus e Patroni via Docker

## Objetivo

Apresentar a tecnologia de banco de dados distribuídos na prática. Diferente de tutoriais automatizados, **nesta versão do laboratório você colocará a mão na massa, digitando e compreendendo cada comando**. Você irá instanciar, popular e testar duas arquiteturas: uma **Monolítica** (PostgreSQL padrão), uma **Distribuída Simples** (PostgreSQL + Citus) e, por fim, entender a configuração de **Alta Disponibilidade** (Citus + Patroni).

Ao final, analisaremos o desempenho e a resiliência dessas arquiteturas para entender os *trade-offs* de cada abordagem.

## Background

### Escalabilidade Vertical vs Horizontal

Para lidar com o aumento de carga em um banco de dados, existem duas abordagens fundamentais:

* **Vertical (Scale-up):** Consiste em adicionar mais recursos físicos (CPU, Memória RAM, armazenamento de Disco) a um único servidor. É uma abordagem arquiteturalmente mais simples, mas foca em melhorar a performance individual da máquina, esbarrando em um teto de hardware (limite físico e custo financeiro exponencial).

* **Horizontal (Scale-out):** Consiste em adicionar mais máquinas (nós) ao sistema. O banco de dados é particionado e a carga de armazenamento e processamento de consultas é dividida entre essas máquinas. Oferece um crescimento quase linear usando hardware comum, mas introduz complexidade na coordenação da rede e nas transações.

> 🖼️ *(Sugestão: Inserir a Figura 2.1 do TG - Horizontal vs. Vertical Scaling)*

### O que é Sharding? (Particionamento Horizontal)

O **Sharding** é a técnica central que viabiliza a escalabilidade horizontal em bancos de dados relacionais. O banco de dados é fatiado em pedaços menores chamados **shards**.

* **Shard Key (Chave de Particionamento):** É a coluna escolhida para definir como os dados serão divididos (ex: `company_id`). Linhas com a mesma chave são roteadas e armazenadas no mesmo shard físico.

* **Co-location:** Se duas tabelas diferentes (ex: `companies` e `campaigns`) forem particionadas pela mesma *Shard Key*, seus dados correspondentes residirão na mesma máquina. Isso permite que operações de `JOIN` sejam feitas localmente e de forma rápida, sem tráfego de rede.

> 🖼️ *(Sugestão: Inserir a Figura 2.2 do TG - Database Sharding)*

### A Arquitetura do Citus

O **Citus** é uma extensão que transforma o PostgreSQL monolítico em um cluster distribuído aplicando sharding de forma transparente.

1. **Coordinator Node (Nó Coordenador):** Ponto de entrada da aplicação. Planeja a execução identificando os shards relevantes, divide a query em sub-tarefas para os workers, e consolida o resultado.

2. **Worker Nodes (Nós Trabalhadores):** Armazenam as partições reais dos dados (shards) e realizam o processamento pesado.

3. **Reference Tables (Tabelas de Referência):** Tabelas pequenas (como dimensões ou categorias). O Citus cria uma cópia inteira delas em *todos* os Workers para facilitar JOINs locais.

> 🖼️ *(Sugestão: Inserir a Figura 3.4 do TG - Diagrama Simplificado da Arquitetura Distribuída)*

### Replicação e Alta Disponibilidade (Patroni)

Um cluster Citus básico possui um problema: se o Coordenador ou um Worker cair, o banco fica offline (Ponto Único de Falha). Para resolver isso, usamos o **Patroni**.

* **Replicação:** Cada nó (seja coordenador ou worker) ganha réplicas (Standbys) que copiam os dados em tempo real.

* **Consenso e Failover:** O Patroni usa um sistema chamado **etcd** (algoritmo Raft) para monitorar quem está vivo. Se o nó "Líder" cair, o etcd detecta e promove uma réplica a novo Líder em segundos, sem intervenção humana.

## Prática: Preparação do Ambiente

**Pré-requisitos:**

* **Git**, **Docker** e **Docker Compose** instalados (no Windows, use o WSL2).

1. Abra seu terminal e clone o repositório base do laboratório:

```bash
git clone [https://github.com/versianix/tg.git](https://github.com/versianix/tg.git)
cd tg
```

> **Atenção:** O repositório possui scripts `dashboard.sh` que automatizam tudo. **Nós NÃO vamos usá-los nesta atividade.** Vamos executar os comandos na mão para entender o que acontece no motor do banco de dados.

## Passo 1: A Arquitetura Monolítica (Baseline)

Primeiro, vamos subir um banco PostgreSQL comum, injetar dados sintéticos e medir seu desempenho.

1. Entre no diretório do banco monolítico:

```bash
cd postgre
```

2. Inicie o container do PostgreSQL em segundo plano:

```bash
docker compose up -d postgres
```

> **O que este comando faz:** O `docker compose` lê o arquivo `docker-compose.yml` e baixa a imagem oficial do PostgreSQL, criando um container chamado `postgres`. A flag `-d` (detached) faz com que ele rode em segundo plano, liberando seu terminal.

3. Vamos configurar o banco de dados e aplicar o schema real do cenário de testes (usando os comandos executados pelo dashboard):

```bash
docker exec pg_standard psql -U postgres -c "CREATE DATABASE benchmark_db"
docker exec -i pg_standard psql -U postgres -d benchmark_db < schema.sql
```

> **O que este comando faz:** Cria o banco `benchmark_db` e injeta a estrutura de tabelas do seu projeto a partir do arquivo `schema.sql`.

4. Em seguida, vamos carregar os dados das planilhas CSV utilizando o script de carga do projeto:

```bash
bash load_data.sh benchmark_db load
```

> **O que este comando faz:** Aciona o script que lê os CSVs da pasta `data` e os insere no banco PostgreSQL.

5. Com o banco populado, vamos executar o teste de carga estressando o banco usando o script de benchmark profissional:

```bash
bash pgbench.sh
bash benchmark_universal.sh
```

>  **O que este comando faz:** Executa uma suíte robusta de testes com múltiplas cargas de trabalho (TPC-B, Select-Only, etc.), integrando medições do Prometheus e gerando um relatório em CSV.
>
> **AÇÃO:** Quando o teste terminar, anote os resultados gerados na pasta de relatórios.

6. Limpe o ambiente monolítico apagando o container e o volume de dados:

```bash
docker compose down -v
```

## Passo 2: A Arquitetura Distribuída (Citus Básico)

Agora vamos fragmentar o banco em 1 Coordenador e 2 Workers. Não teremos réplicas aqui (sem tolerância a falhas).

1. Vá para a pasta do Citus:

```bash
cd ../citus
```

2. Suba o cluster distribuído básico:

```bash
docker compose up -d coordinator worker1 worker2
```

>  **O que este comando faz:** Ao invés de um, estamos subindo **três** containers separados do PostgreSQL com a extensão Citus instalada. Mas, por enquanto, eles não sabem da existência um do outro.

3. Vamos configurar a arquitetura distribuída. Para o Citus Básico, o passo principal é adicionar os workers ao Coordenador (exatamente como o dashboard faz por baixo dos panos):

```bash
docker exec citus_coordinator psql -U postgres -d citus_platform -c "SELECT citus_add_node('worker1', 5432);"
docker exec citus_coordinator psql -U postgres -d citus_platform -c "SELECT citus_add_node('worker2', 5432);"
```

>  **O que este comando faz:** Registra o IP/Host e a porta (5432) dos workers na tabela de metadados do Coordenador. Agora formamos um cluster!

4. Vamos inicializar o schema do Citus e distribuir as tabelas usando o cenário `adtech` (via script do projeto):

```bash
./scripts/schema_manager.sh create adtech
```

>  **O que este comando faz:** Processa as configurações do cenário `adtech` e aplica o DDL no Citus, criando as tabelas já devidamente particionadas (Sharding).

5. Em seguida, vamos importar os dados do cenário para o cluster distribuído:

```bash
./scripts/data_loader.sh load adtech
```

>  **O que este comando faz:** Aciona a leitura sequencial e ordenada dos CSVs gerados, transferindo os dados para o Coordenador, que os espalha imediatamente pelos workers.

6. Agora, rodamos a suite de testes universal do Citus:

```bash
bash benchmark_universal.sh
```

> **AÇÃO:** O script executará queries e testes sobre o ambiente. Quando terminar, anote os resultados gerados na pasta de relatórios. Note que a query bateu no Coordenador, que precisou planejar e rotear o comando via rede para os Workers, antes de devolver o resultado consolidado para você.

7. Limpe o ambiente:

```
docker compose down -v
```

## 🛡️ Passo 3: Alta Disponibilidade (Citus + Patroni)

No Passo 2, se o `citus_coordinator` travasse, seu banco morreria. Para cenários críticos (Bancos, Hospitais, E-commerce), usamos a topologia de Alta Disponibilidade (HA) adicionando o **Patroni** e o **etcd**.

*(Nota: Como subir 14 containers e configurar o etcd na mão leva horas, aqui entenderemos a arquitetura em nível de blocos executando a orquestração via compose).*

1. Ainda na pasta do Citus, inicie o ambiente com Alta Disponibilidade:

```bash
bash simple_setup.sh
```

> 🔍 **O que este comando faz:** O compose levanta três componentes vitais:
>
> * **etcd (Consenso):** 3 containers que formam um júri. Eles monitoram a saúde do banco (algoritmo Raft).
>
> * **PostgreSQL + Patroni:** O Coordenador e os Workers sobem, mas o Patroni gerencia a replicação física (streaming replication). Se temos o `coordinator1` (Líder), teremos o `coordinator2` e `coordinator3` (Réplicas).
>
> * **HAProxy:** Um roteador de rede. Sua aplicação conecta nele, e ele encaminha o tráfego apenas para quem for o Líder no momento.

2. **Simulando um Desastre (Failover):**
   Vamos ver a mágica do Patroni acontecer. Verifique quem é o líder do Coordenador usando a ferramenta do Patroni (`patronictl`):

```bash
docker exec -it citus_coordinator1 patronictl topology
```

> 🔍 **O que este comando faz:** Imprime uma tabela mostrando o estado do cluster. Você verá um nó marcado como `Leader` e outro como `Replica`.

3. "Puxe o cabo de energia" do Líder pausando o container abruptamente:

```bash
docker pause citus_coordinator1
```

4. Rapidamente (dentro de uns 10 segundos), olhe a topologia novamente através do nó 2:

```bash
docker exec -it citus_coordinator2 patronictl topology
```

> 🔍 **A MÁGICA:** Você verá que o `citus_coordinator2`, que antes era uma simples réplica, foi promovido a `Leader`!
> *Como isso aconteceu?* O **etcd** parou de receber o "heartbeat" (pulsação) do nó 1. Ele informou ao Patroni, que tomou a decisão de promover o nó 2. O HAProxy atualizou suas rotas. Tudo isso **sem você ter que digitar nenhuma linha de SQL ou acordar de madrugada para consertar o banco**.

5. Limpe seu ambiente após finalizar:

```bash
docker compose -f docker-compose-patroni.yml down -v
```

## 📊 Passo 4: Análise de Resultados e Questões

Com base na execução que você realizou na sua máquina local e nos conceitos de arquitetura, responda:

**Questão 1:** Olhando os números que você anotou, qual arquitetura (Passo 1: Monolítica ou Passo 2: Distribuída) obteve o maior TPS e a menor latência?

**Questão 2 (O Paradoxo do Overhead Local):** Em laboratórios locais (rodando no seu notebook), é comum que o banco Distribuído tenha um desempenho *inferior* ao Monolítico. Explique por que isso acontece, considerando:

* O que o `citus_coordinator` precisa fazer antes de buscar o dado (planejamento/roteamento de shards).

* Como o tráfego via rede virtual do Docker afeta o tempo de resposta em relação a ler diretamente da memória RAM em um banco monolítico local.

**Questão 3 (O Trade-off da Alta Disponibilidade):** No Passo 3 (Patroni), inserimos replicação de dados e o cluster `etcd` mandando mensagens o tempo todo (heartbeats). Pensando no processo de gravação (INSERT/UPDATE), explique por que uma arquitetura altamente disponível (Passo 3) será naturalmente mais "lenta" (maior latência) do que uma arquitetura distribuída simples (Passo 2).

**Questão 4 (A Virada de Jogo no Servidor):** Em nossa próxima etapa prática, vamos rodar esse mesmo banco distribuído em um servidor corporativo (múltiplas máquinas físicas, 64 cores de CPU, discos SSD independentes).
Se um Monolito chegar a 100% de uso de CPU no servidor, ele não consegue mais crescer. Como o modelo *Worker/Coordinator* do Citus resolverá esse limite físico para suportar o dobro de conexões e dados na semana seguinte?
