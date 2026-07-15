# Consultor Inteligente de Procedimentos Internos

Trabalho avaliativo para a materia de Inteligencia Artificial.

Sistema de onboarding para estagiarios de suporte de TI, com:

- **Trilhas de treinamento** guiadas passo a passo.
- **Simulador de tarefas** que sorteia tickets reais da base.
- **Mentor virtual** (Gemini) que responde duvidas com base nos POPs internos.
- **Busca semantica** via TF-IDF + cosine similarity (nao busca por substring).

## Estrutura

```
.
├── app.py                 # Servidor Flask (entrada principal web)
├── main.py                # CLI legado
├── search.py              # Logica TF-IDF + cosine similarity
├── llm.py                 # Wrapper do Gemini
├── templates/
│   └── chat.html          # Frontend do chat
├── tests/
│   └── test_search.py     # Testes de verdade (unittest)
├── dataset_suporte_interno_sintetico.csv.xls
├── requirements.txt
├── README.md
└── .gitignore
```

## Como executar (interface web)

```bash
pip install -r requirements.txt
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
5. Os top-3 vao no prompt do Gemini, que gera a resposta final.
6. Se a busca semantica nao achar nada acima do limiar (0.1), um fallback
   por palavra-chave e usado antes de pedir para escalar ao Senior.

### Observacao sobre stop words

O scikit-learn nao tem lista de stop words em portugues por padrao, entao
usamos `stop_words='english'`. Isso remove artigos/preposicoes comuns que
poluem o TF-IDF. Para um trabalho academico o ingles serve como filtro
suficiente; para producao o ideal seria usar NLTK com stopwords em PT-BR.

## Sobre a chave da API

A chave do Gemini esta em `llm.py` (hardcoded) por escolha do autor para
o trabalho academico. Em producao, usar variavel de ambiente:

```python
import os
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
```

## Observacoes

- A chave atual e publica no historico do git. Troque antes de qualquer deploy.
- O servidor Flask nao tem autenticacao (uso local apenas).
- O modelo Gemini usado e `gemini-2.0-flash`.
