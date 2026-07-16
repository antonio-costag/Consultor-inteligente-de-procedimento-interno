"""
Le `data/llm_usage.jsonl` (produzido por src/observabilidade.py) e devolve
agregados para o `gerar_html.py` consumir. Nao levanta excecao se o arquivo
nao existir: devolve chaves vazias, e o HTML renderiza estado vazio em vez
de fabricar numeros.

Saida (dict):

    {
      "llm_usage": {
          "disponivel": bool,    # True so se >= 1 evento de LLM
          "n_eventos": int,
          "n_eventos_llm": int,
          "n_eventos_api": int,
          "n_erros": int,
          "total_tokens": int,
          "prompt_tokens_total": int,
          "completion_tokens_total": int,
          "modelos": {"llama-3.1-8b-instant": int, ...},
          "horas": {0: int, 1: int, ..., 23: int},  # chamadas por hora UTC
      },
      "tokens_por_chamada": [
          {"chamada": 1, "prompt": 120, "completion": 80}, ...
      ],
      "latencia_por_metodo": {
          "semantica":  {"p50": ms, "p95": ms, "n": int},
          "palavra_chave": {...},
          "cortesia":    {...},
          "nenhum":      {...},
      },
      "mix_de_metodos": {
          "semantica": int, "palavra_chave": int, "cortesia": int, "nenhum": int,
      },
      "top_scores": [0.0, 0.31, ...],  # similaridades dos top-1
    }
"""

from __future__ import annotations

import json
import os
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, Iterable, List


HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSONL = os.path.join(os.path.dirname(HERE), "data", "llm_usage.jsonl")


def _percentil(valores: List[float], p: float) -> float:
    if not valores:
        return 0.0
    s = sorted(valores)
    if len(s) == 1:
        return round(s[0], 3)
    # metodo linear mais simples
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return round(s[f], 3)
    return round(s[f] + (s[c] - s[f]) * (k - f), 3)


def _carregar_eventos(caminho: str) -> Iterable[Dict[str, Any]]:
    if not os.path.exists(caminho):
        return []
    out: List[Dict[str, Any]] = []
    with open(caminho, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    return out


def agregar(caminho: str = DEFAULT_JSONL) -> Dict[str, Any]:
    """Le o JSONL e devolve o dict pronto para o HTML."""
    eventos = list(_carregar_eventos(caminho))
    vazio = {
        "llm_usage": {
            "disponivel": False,
            "n_eventos": 0,
            "n_eventos_llm": 0,
            "n_eventos_api": 0,
            "n_erros": 0,
            "total_tokens": 0,
            "prompt_tokens_total": 0,
            "completion_tokens_total": 0,
            "modelos": {},
            "horas": {h: 0 for h in range(24)},
        },
        "tokens_por_chamada": [],
        "latencia_por_metodo": {},
        "mix_de_metodos": {},
        "top_scores": [],
    }
    if not eventos:
        return vazio

    n_llm = sum(1 for e in eventos if e.get("endpoint") == "llm")
    n_api = sum(1 for e in eventos if e.get("endpoint") == "api_consulta")
    n_err = sum(1 for e in eventos if not e.get("ok", True))

    # tokens: apenas eventos endpoint=llm
    prompt_total = sum(int(e.get("prompt_tokens", 0) or 0) for e in eventos if e.get("endpoint") == "llm")
    compl_total = sum(int(e.get("completion_tokens", 0) or 0) for e in eventos if e.get("endpoint") == "llm")
    total_tokens = sum(int(e.get("total_tokens", 0) or 0) for e in eventos if e.get("endpoint") == "llm")

    modelos = Counter()
    for e in eventos:
        if e.get("endpoint") == "llm" and e.get("modelo"):
            modelos[e["modelo"]] += 1

    # chamadas por hora (UTC, conforme ts)
    horas = {h: 0 for h in range(24)}
    for e in eventos:
        ts = e.get("ts", "")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            horas[dt.hour] += 1
        except (ValueError, AttributeError):
            pass

    # tokens por chamada (apenas LLM, ok)
    tokens_por_chamada = []
    seq = 0
    for e in eventos:
        if e.get("endpoint") != "llm" or not e.get("ok", True):
            continue
        seq += 1
        tokens_por_chamada.append({
            "chamada": seq,
            "prompt": int(e.get("prompt_tokens", 0) or 0),
            "completion": int(e.get("completion_tokens", 0) or 0),
        })

    # latencia por metodo (p50/p95) -- apenas api_consulta
    lat_por_metodo: Dict[str, List[float]] = defaultdict(list)
    for e in eventos:
        if e.get("endpoint") != "api_consulta":
            continue
        metodo = e.get("metodo") or "nenhum"
        lat_por_metodo[metodo].append(float(e.get("duracao_ms", 0.0) or 0.0))
    latencia_por_metodo = {
        m: {
            "p50": _percentil(v, 0.50),
            "p95": _percentil(v, 0.95),
            "n": len(v),
            "max": round(max(v), 3) if v else 0.0,
        }
        for m, v in lat_por_metodo.items()
    }

    # mix de metodos
    mix = Counter()
    for e in eventos:
        if e.get("endpoint") != "api_consulta":
            continue
        mix[e.get("metodo") or "nenhum"] += 1
    mix_de_metodos = {k: int(v) for k, v in mix.items()}

    # top scores
    top_scores = []
    for e in eventos:
        if e.get("endpoint") != "api_consulta":
            continue
        ts_ = float(e.get("top_score", 0.0) or 0.0)
        if ts_ > 0.0:
            top_scores.append(round(ts_, 4))

    return {
        "llm_usage": {
            "disponivel": n_llm > 0,
            "n_eventos": len(eventos),
            "n_eventos_llm": n_llm,
            "n_eventos_api": n_api,
            "n_erros": n_err,
            "total_tokens": total_tokens,
            "prompt_tokens_total": prompt_total,
            "completion_tokens_total": compl_total,
            "modelos": dict(modelos),
            "horas": horas,
        },
        "tokens_por_chamada": tokens_por_chamada,
        "latencia_por_metodo": latencia_por_metodo,
        "mix_de_metodos": mix_de_metodos,
        "top_scores": top_scores,
    }


if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSONL
    print(json.dumps(agregar(caminho), ensure_ascii=False, default=str))
