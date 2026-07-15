"""
Wrapper do Gemini para geracao de respostas com base em POPs recuperados.

Usado tanto pelo CLI (main.py) quanto pelo servidor Flask (app.py).
"""

import google.generativeai as genai

# Chave de API. Em producao isto deveria vir de variavel de ambiente;
# mantida hardcoded por decisao do usuario para o trabalho academico.
API_KEY = "AIzaSyDkoPFoZp0ZjzaUKqlg5GkKluhBo_hhRU8"
MODELO = "gemini-2.0-flash"

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
    """Inicializa o SDK do Gemini. Chamado uma vez na inicializacao."""
    genai.configure(api_key=API_KEY)


def gerar_resposta(duvida, resultados, top_k=3):
    """Envia o prompt para o Gemini e devolve o texto da resposta."""
    fatos = _formatar_fatos(resultados)
    prompt = PROMPT_TEMPLATE.format(fatos=fatos, duvida=duvida, top_k=top_k)

    model = genai.GenerativeModel(MODELO)
    response = model.generate_content(prompt)
    return response.text, prompt
