"""
Servidor Flask do Consultor Inteligente de Procedimentos Internos.

Endpoints:
    GET  /             -> pagina de chat
    POST /api/consulta -> recebe {"duvida": "..."} e devolve {"resposta": "...", "resultados": [...]}
"""

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

# Carrega .env antes de qualquer import que dependa da chave
load_dotenv()

import llm
import search as search_mod


app = Flask(__name__)

# Estado carregado uma unica vez no startup
busca: search_mod.SemanticSearch | None = None


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
