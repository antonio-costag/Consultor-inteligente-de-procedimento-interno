"""
Servidor Flask do Consultor Inteligente de Procedimentos Internos.

Endpoints:
    GET  /             -> pagina de chat
    POST /api/consulta -> recebe {"duvida": "..."} e devolve {"resposta": "...", "resultados": [...]}
"""

import unicodedata

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

# Carrega .env antes de qualquer import que dependa da chave
load_dotenv()

import llm
import search as search_mod


app = Flask(__name__)

# Estado carregado uma unica vez no startup
busca: search_mod.SemanticSearch | None = None


# ---------------------------------------------------------------------------
# Intencoes sociais: respostas curtas e fixas, sem chamar a LLM nem a busca.
# O conjunto foi montado a mao cobrindo variacoes comuns em PT-BR/EN.
# ---------------------------------------------------------------------------
SAUDACOES = {
    "oi", "ola", "olá", "bom dia", "boa tarde", "boa noite",
    "eai", "e ai", "e aí", "hello", "hi", "hey",
}
CORTESIAS = {
    "obrigado", "obrigada", "valeu", "vlw", "thanks", "thank you",
    "brigadao", "brigadaum", "brigadão", "muito obrigado", "muito obrigada",
    "agradecido", "agradecida", "tmj", "valeu mesmo",
}
DESPEDIDAS = {
    "tchau", "adeus", "bye", "ate mais", "ate logo", "falou", "flw",
    "ate", "goodbye", "bye bye",
}

RESPOSTA_SAUDACAO = (
    "Ola! Sou seu mentor virtual. Descreva o problema ou duvida sobre "
    "procedimentos internos de TI que eu te ajudo."
)
RESPOSTA_CORTESIA = (
    "Por nada! Se tiver mais alguma duvida sobre procedimentos internos, "
    "e so perguntar."
)
RESPOSTA_DESPEDIDA = "Ate logo! Bom trabalho."

# Palavras que NAO invalidam uma cortesia quando acompanhadas de uma ancora
# social. Cobrem artigos, preposicoes, pronomes, intensificadores e termos
# coloquiais ("obrigado pela ajuda", "valeu demais", "oi galera", etc.).
# Substantivos do dominio de TI NAO entram aqui, para nao gerar falso
# positivo em frases mistas ("obrigado, mas e a VPN?").
PALAVRAS_NEUTRAS_SOCIAL = {
    # Artigos e preposicoes
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das", "no", "na", "nos", "nas", "em",
    "por", "pelo", "pela", "pelos", "pelas", "pra", "pro",
    "com", "sem", "para", "ate", "ao", "aos", "à", "às",
    # Pronomes
    "eu", "tu", "voce", "voces", "ele", "ela", "nos", "eles", "elas",
    "me", "te", "se", "lhe", "lhes", "meu", "minha", "seu", "sua",
    "nosso", "nossa", "vosso", "vossa",
    # Conectivos / intensificadores
    "muito", "muita", "mais", "menos", "tao", "tanto", "bastante",
    "mesmo", "mesma", "todos", "todas", "todo", "toda",
    "ja", "ainda", "sempre", "tambem",
    # Coloquiais que aparecem em cortesias
    "amigo", "amiga", "irmao", "irma", "cara", "velho", "velha",
    "ajuda", "forca", "tudo", "nada", "galera", "pessoal", "turma",
    "demais", "pra", "caramba",
    # Verbos auxiliares
    "foi", "e", "ser", "estar", "haver", "ter",
}


def _normalizar_social(texto):
    """Lowercase + remove acentos. Replica a ideia de search._normalizar
    sem acoplar UI a busca semantica."""
    if not texto:
        return ""
    txt = texto.lower()
    txt = "".join(
        c for c in unicodedata.normalize("NFD", txt)
        if unicodedata.category(c) != "Mn"
    )
    txt = txt.replace("!", " ").replace("?", " ").replace(",", " ").replace(".", " ")
    txt = " ".join(txt.split())
    return txt


def _palavras_do_conjunto(conjunto):
    """Acha um conjunto de chaves multi-palavra em um set de palavras unicas.
    Ex: {'ate logo', 'ate'} -> {'ate', 'logo'}."""
    palavras = set()
    for entrada in conjunto:
        palavras.update(entrada.split())
    return palavras


def classificar_intencao_social(texto):
    """Retorna 'saudacao', 'cortesia' ou 'despedida' se o texto for
    EXCLUSIVAMENTE social. Caso contrario, retorna None e o fluxo tecnico
    assume.

    Tres etapas, na ordem:
      1. Match exato multi-palavra: o texto inteiro bate com uma chave
         do conjunto ("bom dia", "ate logo", "muito obrigado").
      2. Match por ancora: pelo menos uma palavra do texto e ancora
         daquela categoria E todas as demais sao ancora ou estao na
         whitelist PALAVRAS_NEUTRAS_SOCIAL ("obrigado pela ajuda",
         "valeu demais", "oi galera").
      3. Nenhuma das anteriores -> None.
    """
    if not texto:
        return None
    normalizado = _normalizar_social(texto)
    if not normalizado:
        return None
    palavras = normalizado.split()
    if not palavras:
        return None

    categorias = (
        ('despedida', DESPEDIDAS),
        ('cortesia', CORTESIAS),
        ('saudacao', SAUDACOES),
    )

    # Etapa 1: match exato multi-palavra
    for categoria, conjunto in categorias:
        if normalizado in conjunto:
            return categoria

    # Etapa 2: match por ancora social + palavras neutras
    for categoria, conjunto in categorias:
        ancoras = _palavras_do_conjunto(conjunto)
        tem_ancora = any(p in ancoras for p in palavras)
        if not tem_ancora:
            continue
        tudo_valido = all(
            p in ancoras or p in PALAVRAS_NEUTRAS_SOCIAL
            for p in palavras
        )
        if tudo_valido:
            return categoria

    return None


def _serializar_resultado(r):
    row = r['row']
    return {
        'similarity': r.get('similarity'),
        'categoria': row.get('Categoria_Problema'),
        'regra': row.get('Regra_POP'),
        'acao': row.get('Acao_Correta_Estagiario'),
        'ticket_id': row.get('Ticket_ID'),
    }


@app.route('/')
def index():
    return render_template('chat.html')


@app.route('/api/consulta', methods=['POST'])
def api_consulta():
    dados = request.get_json(silent=True) or {}
    duvida = (dados.get('duvida') or '').strip()

    if not duvida:
        return jsonify({'erro': 'duvida vazia'}), 400

    intencao = classificar_intencao_social(duvida)
    if intencao is not None:
        resposta_fixa = {
            'saudacao': RESPOSTA_SAUDACAO,
            'cortesia': RESPOSTA_CORTESIA,
            'despedida': RESPOSTA_DESPEDIDA,
        }[intencao]
        return jsonify({
            'resposta': resposta_fixa,
            'resultados': [],
            'metodo': 'cortesia',
        })

    if not busca or not busca.disponivel():
        return jsonify({
            'resposta': 'Base de POPs nao carregada. Contate o administrador.',
            'resultados': [],
            'metodo': 'nenhum',
        }), 500

    resultados, metodo = busca.consulta_completa(duvida, top_k=3)

    try:
        resposta, _ = llm.gerar_resposta(duvida, resultados, top_k=3)
    except Exception as e:
        return jsonify({
            'resposta': f'Erro ao consultar a OpenAI: {e}',
            'resultados': [_serializar_resultado(r) for r in resultados],
            'metodo': metodo,
        }), 502

    return jsonify({
        'resposta': resposta,
        'resultados': [_serializar_resultado(r) for r in resultados],
        'metodo': metodo,
    })


def inicializar():
    global busca
    busca = search_mod.SemanticSearch()
    llm.configurar()
    if busca.disponivel():
        print(f"[OK] Base carregada: {busca.total_documentos()} POPs")
    else:
        print("[AVISO] Dataset nao encontrado")


if __name__ == '__main__':
    inicializar()
    app.run(host='127.0.0.1', port=5000, debug=False)
