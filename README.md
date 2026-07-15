# MBA IA — Pull, Otimização e Avaliação de Prompts (LangChain + LangSmith)

Software que faz **pull** de um prompt de baixa qualidade do LangSmith Prompt Hub,
**refatora/otimiza** com técnicas avançadas de Prompt Engineering, faz **push** da versão
otimizada de volta ao Hub e **avalia** a qualidade com métricas customizadas (Helpfulness,
Correctness, F1-Score, Clarity, Precision), buscando **≥ 0.8 em todas**.

- **LLM (resposta e avaliação):** Google **Gemini `gemini-2.5-flash`** (modelo free)
- **Prompt base:** `leonanluppi/bug_to_user_story_v1`
- **Prompt otimizado:** `diolehner/bug_to_user_story_v2` (público no Hub)

---

## A) Técnicas Aplicadas (Fase 2)

O prompt otimizado (`prompts/bug_to_user_story_v2.yml`) combina **4 técnicas**. O desafio
exige Few-shot + pelo menos uma adicional; usamos quatro por reforçarem umas às outras
nesta tarefa de raciocínio + formatação estruturada.

### 1. Role Prompting (persona)
**O que é:** definir uma persona e contexto detalhados para o modelo.
**Por que escolhi:** transformar bug em User Story é trabalho de produto; dar ao modelo a
identidade de *Product Manager Sênior ágil* melhora tom, vocabulário e foco em valor de
negócio — exatamente o que as métricas de Tone e Clarity avaliam.
**Como apliquei:** o system prompt abre com
`"Você é um Product Manager Sênior especialista em metodologias ágeis..."` e fixa idioma
(português) e formato (Markdown).

### 2. Few-shot Learning (obrigatória)
**O que é:** fornecer exemplos claros de entrada→saída.
**Por que escolhi:** é o que mais move a agulha aqui — o avaliador compara a resposta com
uma referência de formato bem específico (template de User Story + critérios Dado/Quando/
Então + contexto técnico). Mostrar exemplos alinha a saída ao ground truth, elevando
F1-Score e Precision.
**Como apliquei:** 3 exemplos cobrindo os níveis de complexidade do dataset:
- **Simples** (botão de carrinho) → User Story + 5 critérios;
- **Médio** (falha de autorização em `/api/users/:id`) → + seção *Contexto de Segurança*;
- **Complexo** (checkout com 4 falhas) → estrutura seccionada completa.

### 3. Chain of Thought (CoT)
**O que é:** instruir o modelo a "pensar passo a passo" antes de responder.
**Por que escolhi:** bugs médios/complexos exigem análise (identificar complexidade,
persona, valor, critérios, contexto técnico). Raciocinar antes reduz omissões e melhora
Completeness e Correctness.
**Como apliquei:** seção *"Raciocínio (pense passo a passo)"* com 5 etapas, seguida da
instrução de **não expor** o raciocínio e entregar só a User Story final.

### 4. Skeleton of Thought
**O que é:** estruturar a resposta em um esqueleto de seções claras.
**Por que escolhi:** consistência estrutural é diretamente medida (User Story Format,
Acceptance Criteria, Clarity). Um esqueleto fixo, adaptável à complexidade, mantém a saída
previsível e comparável à referência.
**Como apliquei:** esqueleto obrigatório *User Story → Critérios de Aceitação → Contexto
Técnico/Segurança → (para bugs complexos) seções `===` com Tasks Técnicas*.

> **System vs User prompt:** o *system* carrega persona, regras, raciocínio e exemplos
> (sem variáveis); o *user* contém apenas o `{bug_report}`. Isso corrige o principal
> problema do v1, que duplicava `{bug_report}` em system e user e não tinha persona.

---

## B) Resultados Finais

**Dashboard LangSmith (público):**
- Prompt v2: https://smith.langchain.com/prompts/bug_to_user_story_v2
- Projeto de avaliação: `prompt-optimization-challenge` em https://smith.langchain.com

### Tabela comparativa v1 (ruim) vs v2 (otimizado)

| Métrica      | v1 (ilustrativo) | v2 (obtido) | Status |
|--------------|:----------------:|:-----------:|:------:|
| Helpfulness  | 0.45             | _<preencher>_ | _<>_ |
| Correctness  | 0.52             | _<preencher>_ | _<>_ |
| F1-Score     | 0.48             | _<preencher>_ | _<>_ |
| Clarity      | 0.50             | _<preencher>_ | _<>_ |
| Precision    | 0.46             | _<preencher>_ | _<>_ |

> Métricas derivadas: `Helpfulness = (Clarity + Precision)/2`,
> `Correctness = (F1 + Precision)/2`. Critério de aprovação: **todas ≥ 0.8**.

_Screenshots das avaliações e do tracing de exemplos: ver pasta `screenshots/`._

---

## C) Como Executar

### Pré-requisitos
- Python 3.9+
- Conta no [LangSmith](https://smith.langchain.com) com API Key e handle (username) definidos
- API Key do [Google AI Studio](https://aistudio.google.com/app/apikey) (Gemini, free)

### Setup
```bash
python3 -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # preencha as credenciais
```

`.env` (valores principais):
```
LANGSMITH_API_KEY=...              # sua chave do LangSmith
USERNAME_LANGSMITH_HUB=diolehner   # seu handle do Hub
GOOGLE_API_KEY=...                 # sua chave do Gemini
LLM_PROVIDER=google
LLM_MODEL=gemini-2.5-flash
EVAL_MODEL=gemini-2.5-flash
```

### Fases do projeto
```bash
# 1. Pull do prompt ruim (leonanluppi/bug_to_user_story_v1)
python src/pull_prompts.py

# 2. Otimização: editar prompts/bug_to_user_story_v2.yml (já incluso, otimizado)

# 3. Push do prompt otimizado ao Hub (público)
python src/push_prompts.py

# 4. Avaliação automática (métricas via LLM-as-Judge)
python src/evaluate.py

# Testes de validação do prompt
pytest tests/test_prompts.py -v
```

---

## Estrutura

```
├── prompts/
│   ├── bug_to_user_story_v1.yml   # prompt inicial (pull do Hub)
│   └── bug_to_user_story_v2.yml   # prompt otimizado (nosso)
├── datasets/bug_to_user_story.jsonl   # 15 bugs (5 simples, 7 médios, 3 complexos)
├── src/
│   ├── pull_prompts.py   # pull do Hub (implementado)
│   ├── push_prompts.py   # push ao Hub (implementado)
│   ├── evaluate.py       # avaliação (pronto)
│   ├── metrics.py        # 5 métricas (pronto)
│   └── utils.py          # auxiliares (pronto)
└── tests/test_prompts.py # 6 testes de validação (implementado)
```

## Nota sobre o provider
Este projeto usa **Gemini (free)** tanto para responder quanto para avaliar
(`LLM_PROVIDER=google`). O código também suporta OpenAI (`gpt-4o-mini` / `gpt-4o`)
trocando as variáveis no `.env`.
