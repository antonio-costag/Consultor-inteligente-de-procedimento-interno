# Consultor Inteligente de Procedimentos Internos[cite: 21]

> **"Onboarding interativo e mentoria em TI via RAG para estagiários."**

Trabalho avaliativo para a matéria de Inteligência Artificial (CC0121) do Bacharelado em Ciência da Computação da Universidade Federal do Amapá (UNIFAP)[cite: 21].

---

## 👥 Equipe
* **Antônio Neto Pereira da Costa** - Desenvolvedor Backend / Integração de IA e Busca Semântica[cite: 21]
* **Rodrigo Ryan Lemos Ribeiro** - [Adicione o papel específico aqui][cite: 21]
* **Breno Gabriel de Moraes Duarte** - [Adicione o papel específico aqui][cite: 21]
* **Gabriel Canto Goes** - [Adicione o papel específico aqui][cite: 21]
* **Orientador:** Prof. Adolfo Colares[cite: 21]

## 🚨 O Problema
O processo de integração (*onboarding*) de novos colaboradores de TI é historicamente marcado por insegurança e ineficiência, gerando um problema bidirecional[cite: 21]:
1. **Gargalo de Autonomia (O Estagiário):** Diante de fluxos implícitos e jargões desconhecidos, o estagiário desenvolve medo de errar[cite: 21]. Soluções como manuais em PDF de 80 páginas possuem baixíssima adotabilidade por exigirem buscas passivas e exaustivas[cite: 21].
2. **Sobrecarga das Lideranças:** Ao não encontrar respostas, o estagiário interrompe os analistas Sêniores[cite: 21]. Essas quebras de foco (*context switching*) degradam a produtividade estratégica de toda a equipe de liderança[cite: 21].

## 💡 A Solução
Substituir a busca passiva tradicional por uma interface conversacional ativa e inteligente[cite: 21]. O sistema atua como um **Mentor Virtual** que lê, compreende a intenção de perguntas informais usando Processamento de Linguagem Natural (PLN) e sintetiza a resposta em tempo real com base oficial nos Procedimentos Operacionais Padrão (POPs)[cite: 21]. 

<video src="demonstracoes/chat%20eduerom.mp4" width="60%" controls>
  Seu navegador não suporta a tag de vídeo.
</video>

<video src="demonstracoes/interacao%20natural.mp4" width="60%" controls>
  Seu navegador não suporta a tag de vídeo.
</video>



## 📊 Dados
* **Fonte e Tamanho:** O projeto utiliza um *dataset* sintético (`dataset_suporte_interno_sintetico.csv.xls`) simulando uma base de conhecimento de suporte de TI universitário (ex: PROGEP, DERCA, EDUROAM), totalizando 500 linhas[cite: 21].
* **O que a EDA revelou:** A Análise Exploratória de Dados revelou inconsistências de *encoding*, presença de caracteres especiais e um severo desbalanceamento de redundância (ex: 109 linhas repetindo o exato mesmo texto para a mesma categoria)[cite: 21]. Esse comportamento viciaria a busca semântica, forçando o LLM à generalização em vez de precisão[cite: 21].
* **Tratamento de Problemas:** 
  * *Redundância:* Desenvolvemos o script `atualizar_dataset.py` para gerar 5 variações textuais de cada regra por categoria, diversificando o vocabulário e balanceando o *dataset*[cite: 21].
  * *Valores Faltantes e Normalização:* Como os dados são estritamente textuais ("zeros impossíveis" não se aplicam), aplicamos a limpeza removendo pontuações e normalizando caracteres Unicode com decomposição NFD para remover acentuações[cite: 21].
  * *Ruído:* Implementamos a exclusão de *stop words* (em inglês via `scikit-learn` como aproximação acadêmica) e utilizamos bigramas (ex: "software pirata") para garantir a fidelidade do vocabulário corporativo[cite: 21].

## 🧠 Metodologia
* **Técnicas Testadas:** O projeto comparou a Busca Literal clássica (filtro rígido via `str.contains`) contra a Busca Semântica usando *TF-IDF* aliada ao padrão *Retrieval-Augmented Generation (RAG)*[cite: 21].
* **Por que escolheram a final:** A combinação **TF-IDF + LLM (llama-3.1-8b-instant)** foi a vencedora porque contorna limitações de vocabulário exato. Se o estagiário pesquisar "wifi", o sistema calcula a distância matemática no espaço vetorial e recupera com sucesso o POP de "EDUROAM"[cite: 21].
* **Divisão Treino/Teste:** Uma vez que utilizamos algoritmos não supervisionados para recuperação de informação (TF-IDF) em conjunto com um LLM pré-treinado, a clássica divisão de treino e teste não se aplica[cite: 21]. O modelo foi validado através de simulações com testes unitários automatizados (`tests/test_search.py`)[cite: 21].
* **Como evitaram overfitting (Alucinação):** Na IA Generativa, o viés de superajuste se traduz na "alucinação" de informações de fora da base. Evitamos isso parametrizando a `temperature` do LLM para `0.2` (saída mais determinística) e blindando o *System Prompt* com a instrução `=== REGRA ABSOLUTA DE OURO ===`, forçando o sistema a usar estritamente o contexto fornecido[cite: 21].

## 📈 Resultados e Métricas
* **Métrica Escolhida:** O **Cosine Similarity Score** (Similaridade de Cosseno) foi escolhido pois o objetivo principal num sistema RAG é recuperar os documentos com a melhor proximidade semântica angular em relação à dúvida do usuário. Foi definido um *threshold* de corte de `0.05` para mitigar falsos positivos de documentos[cite: 21].
* **Matriz de Confusão Equivalente:** A validação ocorreu nos testes unitários:
  * *Verdadeiro Positivo:* Consultas com termos como "impressora com defeito" recuperam com sucesso os documentos corretos com similaridade superior a 10%[cite: 21].
  * *Verdadeiro Negativo:* Consultas vazias ou com jargões completamente desconexos não retornam resultados[cite: 21].
* **Comparação / Arquitetura:** O modelo em cascata (*fallback*) provou-se superior: ele prioriza a Busca Semântica (TF-IDF), mas caso ocorra uma falha de limiar de similaridade, ele aciona a Busca Literal como *fallback* antes de pedir intervenção humana, garantindo precisão absoluta[cite: 21].

## ⚖️ Ética, Vieses e Próximos Passos
O sistema identificou vulnerabilidades relacionadas ao viés de linguagem corporativa, onde estagiários utilizando gírias ou dialetos não abrangidos nos dados de pré-treino podem ter suas dúvidas mal compreendidas[cite: 21]. O modelo também carece de raciocínio lógico independente de sua base vetorial[cite: 21]. Como evolução, o projeto prevê a migração do TF-IDF para um banco de dados vetorial dedicado (ex: ChromaDB) e a implementação de um *pipeline* de aprendizado ativo para o setor de RH auditar *queries* de baixa similaridade[cite: 21].

---

## 🚀 Como Rodar (Passo a Passo)

Testado e validado em ambiente limpo:

1. **Clone o repositório e acesse a pasta:**
   ```bash
   git clone <link-do-repositorio>
   cd <nome-da-pasta>

# Consultor Inteligente de Procedimentos Internos

Trabalho avaliativo para a materia de Inteligencia Artificial.

Sistema de onboarding para estagiarios de suporte de TI, com:

- **Trilhas de treinamento** guiadas passo a passo.
- **Simulador de tarefas** que sorteia tickets reais da base.
- **Mentor virtual** (Groq llama-3.1-8b-instant) que responde duvidas com base nos POPs internos.
- **Busca semantica** via TF-IDF + cosine similarity (nao busca por substring).

## Estrutura

```
meu-projeto-ia/
├── README.md                       # A vitrine do projeto (este arquivo)
├── notebooks/
│   └── desenvolvimento.ipynb       # EDA, experimentos e treino do modelo
├── src/
│   └── app.py                      # Código organizado (app, funções, pipeline)
├── data/                           # Dados brutos e tratados (ou instruções de download)
├── relatorio/
│   └── relatorio_tecnico.pdf       # Relatório técnico do projeto
├── slides/
│   └── pitch.pdf                   # Slides de apresentação
└── requirements.txt                # Dependências para reproduzir o ambiente
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
