"""
Observabilidade minima do Consultor Inteligente.

Captura uso da LLM (Groq) e latencia do endpoint /api/consulta em
`data/llm_usage.jsonl` (uma linha JSON por evento). Nao depende de servico
externo, nao bloqueia a requisicao em caso de falha de IO.

Schema de cada linha:

    {
      "ts": "2026-07-16T14:23:45.123Z",   # ISO 8601 UTC
      "endpoint": "api_consulta",          # ou "llm"
      "metodo": "semantica",               # semantica | palavra_chave | cortesia | nenhum
      "modelo": "llama-3.1-8b-instant",    # string do provider, "" se nao usou LLM
      "ok": true,                          # false se houve excecao
      "erro": "",                          # string do tipo de erro, "" se ok
      "duracao_ms": 312.4,                 # float, perf_counter
      "prompt_tokens": 0,                  # int, 0 se nao usou LLM
      "completion_tokens": 0,
      "total_tokens": 0,
      "top_score": 0.0,                    # similaridade do top-1, NaN se nao houve
    }

Uso:

    from observabilidade import registrar_chamada_llm

    @registrar_chamada_llm
    def gerar_resposta(...): ...

E em api_consulta:

    from observabilidade import MetricsStore
    MetricsStore.instance().log({
        "endpoint": "api_consulta",
        "metodo": metodo,
        "duracao_ms": ...,
        ...
    })
"""

from __future__ import annotations

import json
import os
import threading
import time
import traceback
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, Optional


DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "llm_usage.jsonl",
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"


def _safe_exc_type(e: BaseException) -> str:
    return type(e).__name__


class MetricsStore:
    """Append-only JSONL writer com lock para uso multi-thread do Flask.

    Singleton preguiçoso: `MetricsStore.instance()` retorna o mesmo
    `MetricsStore` para todo o processo. O lock protege o `write()`; o resto
    do codigo nao bloqueia.
    """

    _instance: Optional["MetricsStore"] = None
    _instance_lock = threading.Lock()

    def __init__(self, path: str = DEFAULT_PATH) -> None:
        self.path = path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(path), exist_ok=True)

    @classmethod
    def instance(cls) -> "MetricsStore":
        if cls._instance is not None:
            return cls._instance
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def log(self, event: Dict[str, Any]) -> None:
        """Grava um evento no JSONL. Falhas de IO NAO propagam."""
        try:
            # sem `default=str`: queremos FALHAR em chaves nao serializaveis
            # para que um bug que injete `object()`/`set()` nao seja
            # silenciosamente convertido em "<object object at 0x...>".
            line = json.dumps(event, ensure_ascii=False)
        except (TypeError, ValueError):
            # evento nao serializavel: ignora silenciosamente
            return
        try:
            with self._lock:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
        except OSError:
            # filesystem indisponivel: nao derruba a app
            pass


def registrar_chamada_llm(func: Callable) -> Callable:
    """Decorator para `llm.gerar_resposta`.

    Mede duracao, captura `response.usage` se a funcao retornar um objeto
    Groq-like (ou um dict com chaves `usage`/`prompt_tokens`), e loga
    o evento. Preserva a assinatura original.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        store = MetricsStore.instance()
        t0 = time.perf_counter()
        ok = True
        err = ""
        result: Any = None
        try:
            result = func(*args, **kwargs)
        except BaseException as e:  # noqa: BLE001
            ok = False
            err = _safe_exc_type(e)
            # loga o erro mesmo sem conseguir extrair tokens
            store.log({
                "ts": _utcnow_iso(),
                "endpoint": "llm",
                "metodo": "",
                "modelo": "",
                "ok": False,
                "erro": err,
                "duracao_ms": round((time.perf_counter() - t0) * 1000, 3),
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "top_score": 0.0,
            })
            raise

        # Sucesso: extrai tokens do retorno.
        # A funcao decorada pode devolver:
        #   - o objeto Response da Groq (com .usage)
        #   - uma tupla (texto, prompt[, usage])
        prompt_tokens = completion_tokens = total_tokens = 0
        modelo = ""
        usage_obj: Any = None
        if isinstance(result, tuple):
            if len(result) >= 3 and isinstance(result[2], dict):
                usage_obj = result[2]
            # se a funcao decorada for a versao antiga (texto, prompt), nao ha tokens
        else:
            # objeto Response-like
            usage_obj = getattr(result, "usage", None)
            modelo = getattr(result, "model", "") or ""

        if usage_obj is not None:
            if isinstance(usage_obj, dict):
                prompt_tokens = int(usage_obj.get("prompt_tokens", 0) or 0)
                completion_tokens = int(usage_obj.get("completion_tokens", 0) or 0)
                total_tokens = int(usage_obj.get("total_tokens", 0) or 0)
            else:
                prompt_tokens = int(getattr(usage_obj, "prompt_tokens", 0) or 0)
                completion_tokens = int(getattr(usage_obj, "completion_tokens", 0) or 0)
                total_tokens = int(getattr(usage_obj, "total_tokens", 0) or 0)

        store.log({
            "ts": _utcnow_iso(),
            "endpoint": "llm",
            "metodo": "",
            "modelo": modelo,
            "ok": True,
            "erro": "",
            "duracao_ms": round((time.perf_counter() - t0) * 1000, 3),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "top_score": 0.0,
        })
        return result

    return wrapper


def log_request(
    *,
    metodo: str,
    duracao_ms: float,
    top_score: float = 0.0,
    ok: bool = True,
    erro: str = "",
) -> None:
    """Atalho para gravar um evento de /api/consulta."""
    MetricsStore.instance().log({
        "ts": _utcnow_iso(),
        "endpoint": "api_consulta",
        "metodo": metodo,
        "modelo": "",
        "ok": ok,
        "erro": erro,
        "duracao_ms": round(float(duracao_ms), 3),
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "top_score": round(float(top_score), 4) if top_score == top_score else 0.0,
    })


def path_jsonl() -> str:
    """Caminho default do JSONL (util para coletor/HTML)."""
    return DEFAULT_PATH


__all__ = [
    "MetricsStore",
    "registrar_chamada_llm",
    "log_request",
    "path_jsonl",
]
