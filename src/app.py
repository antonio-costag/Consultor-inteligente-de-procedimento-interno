"""
Shim de compatibilidade.

O servidor Flask vive em ``main.py`` (nome curto, convenção do projeto),
mas a suíte de testes em ``tests/test_app.py`` importa ``app``. Este
módulo apenas reexporta o que os testes esperam.
"""

import llm
import search as search_mod  # reexporta o módulo de busca

from main import (  # noqa: F401,F403
    app,
    classificar_intencao_social,
    inicializar,
    SAUDACOES,
    CORTESIAS,
    DESPEDIDAS,
    PALAVRAS_NEUTRAS_SOCIAL,
    RESPOSTA_SAUDACAO,
    RESPOSTA_CORTESIA,
    RESPOSTA_DESPEDIDA,
    _normalizar_social,
    _palavras_do_conjunto,
    _serializar_resultado,
)

# Exposição usada pelos testes que mockam `app.llm.gerar_resposta`.
# Em main.py o módulo é importado como `llm` (atributo `main.llm`).
# Mantemos também como `app.llm` para casar com o mock.
