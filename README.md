# Consultor Inteligente de Procedimentos Internos

Trabalho avaliativo para a materia de Inteligencia Artificial.

Sistema de onboarding para estagiarios de suporte de TI, com:

- **Trilhas de treinamento** guiadas passo a passo.
- **Simulador de tarefas** que sorteia tickets reais da base.
- **Mentor virtual** (Groq llama-3.1-8b-instant) que responde duvidas com base nos POPs internos.
- **Busca semantica** via TF-IDF + cosine similarity (nao busca por substring).

## Estrutura

```
.
├── app.py                 # Servidor Flask (entrada principal web)
├── main.py                # CLI legado
├── search.py              # Logica TF-IDF + cosine similarity
├── llm.py                 # Wrapper do Groq (llama-3.1-8b-instant)
├── templates/
│   └── chat.html          # Frontend do chat
├── tests/
│   └── test_search.py     # Testes de verdade (unittest)
├── dataset_suporte_interno_sintetico.csv.xls
├── requirements.txt
├── .env.example           # Modelo do arquivo de variaveis de ambiente
├── README.md
└── .gitignore
```

## Como executar (interface web)

```bash
pip install -r requirements.txt
cp .env.example .env       # e cole sua chave Groq no .env
python app.py
```

Abrir `http://localhost:5000` no navegador.

## Como executar (CLI)

```bash
python main.py
```

## Como rodar os testes

```bash
python -m unittest discover tests
```

## Como funciona a busca semantica

1. Cada POP do CSV vira um documento: `Categoria + Regra + Descricao`.
2. TF-IDF vetoriza os documentos (unigramas + bigramas, max 1000 features).
3. A duvida do usuario e vetorizada no mesmo espaco.
4. Cosine similarity ranqueia os POPs mais relevantes.
5. Os top-3 vao no prompt do llama-3.1-8b-instant, que gera a resposta final.
6. Se a busca semantica nao achar nada acima do limiar (0.1), um fallback
   por palavra-chave e usado antes de pedir para escalar ao Senior.

### Observacao sobre stop words

O scikit-learn nao tem lista de stop words em portugues por padrao, entao
usamos `stop_words='english'`. Isso remove artigos/preposicoes comuns que
poluem o TF-IDF. Para um trabalho academico o ingles serve como filtro
suficiente; para producao o ideal seria usar NLTK com stopwords em PT-BR.

## Sobre a chave da API

A chave do Groq e lida da variavel de ambiente `GROQ_API_KEY`. Crie um arquivo
`.env` na raiz do projeto com o conteudo:

```
GROQ_API_KEY=gsk_sua_chave_aqui
```

O `.env` ja esta no `.gitignore` e nao sera commitado. Para producao, prefira
injetar a variavel direto no ambiente do servidor.

## Por que Groq e nao OpenAI

O Groq oferece um free tier generoso para o modelo `llama-3.1-8b-instant`,
sem necessidade de cartao de credito. A API do Groq e compativel com a
interface de chat da OpenAI, entao a integracao foi feita com o SDK oficial
do Groq. Se quiser usar OpenAI depois, basta restaurar a versao anterior
do `llm.py`.

## Observacoes

- O servidor Flask nao tem autenticacao (uso local apenas).
- O modelo LLM usado e `llama-3.1-8b-instant` via Groq.
- Historico: este projeto ja utilizou OpenAI em uma versao anterior; a chave
  da OpenAI foi removida do codigo. Caso veja referencias antigas em commits
  passados, **revogue a chave no painel da OpenAI** se ainda nao o fez.
