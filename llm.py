"""
Wrapper do Groq (llama-3.1-8b-instant) para geracao de respostas com base
em POPs recuperados.

Usado tanto pelo CLI (main.py) quanto pelo servidor Flask (app.py).

A chave da API e lida da variavel de ambiente GROQ_API_KEY. Crie um arquivo
.env na raiz do projeto com:

    GROQ_API_KEY=gsk_sua_chave_aqui

O .env ja esta no .gitignore e nao sera commitado.
"""

import os

from groq import Groq

API_KEY = os.environ.get("GROQ_API_KEY", "")
MODELO = "llama-3.1-8b-instant"

PROMPT_TEMPLATE = """Voce e um Consultor Inteligente de Procedimentos Internos
ajudando um estagiario de suporte de TI. Responda a duvida do estagiario de forma
direta, clara e profissional.

Regra Fundamental: BASEIE SUA RESPOSTA EXCLUSIVAMENTE NOS PROCEDIMENTOS ABAIXO.
Se a solucao nao estiver nos procedimentos, instrua o estagiario a escalar o
ticket para um analista Senior.

PROCEDIMENTOS INTERNOS RECUPERADOS (top {top_k} via busca semantica):
{fatos}

DUVIDA DO ESTAGIARIO:
"{duvida}"
"""


def _formatar_fatos(resultados):
    """Converte a lista de resultados da busca em texto para o prompt."""
    if not resultados:
        return "- Nenhum procedimento especifico encontrado na base local. Aja com bom senso ou escale ao Senior."
    linhas = []
    for r in resultados:
        row = r['row']
        sim = r.get('similarity')
        if sim is not None:
            linhas.append(
                f"- Categoria: {row['Categoria_Problema']} | "
                f"Regra: {row['Regra_POP']} | "
                f"Acao Recomendada: {row['Acao_Correta_Estagiario']} "
                f"(Similaridade: {sim:.2f})"
            )
        else:
            linhas.append(
                f"- Categoria: {row['Categoria_Problema']} | "
                f"Regra: {row['Regra_POP']} | "
                f"Acao Recomendada: {row['Acao_Correta_Estagiario']}"
            )
    return "\n".join(linhas)


def configurar():
    """Inicializacao lazy. Apenas avisa se a chave nao estiver configurada."""
    if not API_KEY:
        print("[AVISO] GROQ_API_KEY nao definida. Crie um .env ou exporte a variavel.")
    return None


def gerar_resposta(duvida, resultados, top_k=3):
    """Envia o prompt para o llama-3.1-8b-instant (via Groq) e devolve o texto."""
    if not API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY nao configurada. Crie um .env na raiz do projeto "
            "com a linha: GROQ_API_KEY=gsk_sua_chave"
        )

    fatos = _formatar_fatos(resultados)
    prompt = PROMPT_TEMPLATE.format(fatos=fatos, duvida=duvida, top_k=top_k)

    client = Groq(api_key=API_KEY)
    response = client.chat.completions.create(
        model=MODELO,
        messages=[
            {
                "role": "system",
                "content": (
                    "Voce e um Consultor Inteligente de Procedimentos Internos "
                    "que responde com base exclusivamente nos POPs fornecidos."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content, prompt
