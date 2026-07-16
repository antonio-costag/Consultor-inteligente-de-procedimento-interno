"""
Coleta metricas reais do projeto para alimentar os graficos:

- Tempos por teste (unittest) -> barras horizontais
- Distribuicao do dataset por categoria -> barra vertical + pizza
- Cobertura do classificador de intencao social -> barras empilhadas
- Distribuicao de similaridade do TF-IDF em consultas tipicas -> histograma
- Volume de codigo (LoC) por modulo -> barra horizontal
- Matriz de confusao equivalente (TP/TN/FP/FN) por suite -> barra agrupada

Tudo impresso em JSON unico no stdout. A pagina HTML abaixo consome esse JSON
e renderiza graficos SVG puros (sem libs externas).
"""

import json
import os
import re
import sys
import time
import unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import pandas as pd  # noqa: E402

import search as search_mod  # noqa: E402
import app as app_mod  # noqa: E402


# ---------------------------------------------------------------------------
# 1) Tempos por teste
# ---------------------------------------------------------------------------
def collect_test_times():
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(ROOT, "tests"))

    state = {"_t0": 0.0, "current": None}
    results = []

    class TimingResult(unittest.TestResult):
        def startTest(self, test):
            super().startTest(test)
            state["_t0"] = time.perf_counter()
            state["current"] = test

        def stopTest(self, test):
            super().stopTest(test)
            dt = (time.perf_counter() - state["_t0"]) * 1000.0
            results.append({
                "id": test.id(),
                "short": test._testMethodName,
                "module": test.__class__.__module__.replace("test_", "").replace("tests.", ""),
                "class": test.__class__.__name__,
                "ms": round(dt, 3),
                "ok": test in self.successes if hasattr(self, "successes") else True,
            })

    runner = unittest.TextTestRunner(resultclass=TimingResult, stream=open(os.devnull, "w"), verbosity=0)
    runner.run(suite)
    return results


# ---------------------------------------------------------------------------
# 2) Distribuicao do dataset por categoria
# ---------------------------------------------------------------------------
def collect_dataset_distribution():
    csv_path = os.path.join(ROOT, "data", "dataset_suporte_interno_sintetico.csv.xls")
    df = pd.read_csv(csv_path, sep=";", encoding="latin-1")
    counts = df["Categoria_Problema"].value_counts().to_dict()
    counts = {str(k): int(v) for k, v in counts.items()}
    return {"total": int(len(df)), "by_category": counts}


# ---------------------------------------------------------------------------
# 3) Cobertura do classificador de intencao social
# ---------------------------------------------------------------------------
def collect_social_classifier():
    casos = {
        "saudacao": [
            "oi", "Ola!", "bom dia",
            "oi galera", "bom dia meu amigo", "olá!",
        ],
        "cortesia": [
            "obrigado", "Obrigado!", "muito obrigado", "valeu",
            "obrigado pela ajuda", "valeu demais", "brigadao pela forca",
            "obrigado amigo", "muito obrigado mesmo", "OBRIGADO",
        ],
        "despedida": [
            "tchau", "Ate logo!", "tchau pessoal", "ate mais galera",
        ],
        "mista": [
            "obrigado, mas e a VPN?",
            "valeu, mas a impressora nao funciona",
            "oi, como configuro o wifi?",
        ],
    }
    rows = []
    for esperado, exemplos in casos.items():
        for ex in exemplos:
            obtido = app_mod.classificar_intencao_social(ex)
            rows.append({"esperado": esperado, "obtido": obtido, "frase": ex})
    return rows


# ---------------------------------------------------------------------------
# 4) Distribuicao de similaridade do TF-IDF
# ---------------------------------------------------------------------------
def collect_similarity_distribution():
    s = search_mod.SemanticSearch()
    consultas = [
        "impressora com defeito",
        "wifi nao conecta",
        "vpn corporativa",
        "senha do eduroam invalida",
        "software pirata instalacao",
        "acesso ao cafe dos professores",
        "visita do loco",
        "impressora travando",
        "esqueci a senha do sistema",
        "problema de suporte",
        "equipamento de impressao quebrado",
        "minha VPN nao conecta",
        "como configuro o email",
        "computador nao liga",
        "site da universidade fora do ar",
    ]
    pontos = []
    for q in consultas:
        resultados = s.buscar(q, top_k=3)
        for r in resultados:
            pontos.append({"query": q, "score": round(r["similarity"], 4)})
    return pontos


# ---------------------------------------------------------------------------
# 5) LoC por arquivo de codigo
# ---------------------------------------------------------------------------
def collect_loc():
    arquivos = {
        "src/main.py": 0,
        "src/search.py": 0,
        "src/llm.py": 0,
        "src/cli.py": 0,
        "src/atualizar_dataset.py": 0,
        "src/app.py": 0,
        "tests/test_search.py": 0,
        "tests/test_app.py": 0,
    }
    for rel in arquivos:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            texto = f.read()
        linhas = [ln for ln in texto.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        arquivos[rel] = len(linhas)
    return arquivos


# ---------------------------------------------------------------------------
# 6) Matriz de confusao equivalente (TP/TN/FP/FN) por suite
# ---------------------------------------------------------------------------
def collect_confusion():
    s = search_mod.SemanticSearch()
    positivos = [
        "impressora com defeito",
        "wifi nao conecta",
        "vpn corporativa",
        "senha do eduroam invalida",
        "software pirata instalacao",
    ]
    negativos = [
        "gosto de pizza",
        "como esta o tempo hoje",
        "musica preferida rock",
        "vou viajar amanha",
    ]
    TP = FP = TN = FN = 0
    for q in positivos:
        r = s.buscar(q, top_k=3)
        if r and r[0]["similarity"] >= 0.10:
            TP += 1
        else:
            FN += 1
    for q in negativos:
        r = s.buscar(q, top_k=3)
        if r and r[0]["similarity"] >= 0.10:
            FP += 1
        else:
            TN += 1
    precisao = TP / (TP + FP) if (TP + FP) else 0
    revocacao = TP / (TP + FN) if (TP + FN) else 0
    f1 = (2 * precisao * revocacao / (precisao + revocacao)) if (precisao + revocacao) else 0
    return {
        "TP": TP, "FP": FP, "TN": TN, "FN": FN,
        "precision": round(precisao, 3),
        "recall": round(revocacao, 3),
        "f1": round(f1, 3),
    }


# ---------------------------------------------------------------------------
# 7) Volume de testes por classe
# ---------------------------------------------------------------------------
def collect_tests_by_class():
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(ROOT, "tests"))
    by = Counter()
    for t in suite:
        if isinstance(t, unittest.TestSuite):
            for sub in t:
                if isinstance(sub, unittest.TestSuite):
                    for case in sub:
                        if isinstance(case, unittest.TestCase):
                            by[case.__class__.__name__] += 1
                elif isinstance(sub, unittest.TestCase):
                    by[sub.__class__.__name__] += 1
    return dict(by)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    out = {
        "test_times": collect_test_times(),
        "dataset": collect_dataset_distribution(),
        "social": collect_social_classifier(),
        "similarity": collect_similarity_distribution(),
        "loc": collect_loc(),
        "confusion": collect_confusion(),
        "tests_by_class": collect_tests_by_class(),
    }
    print(json.dumps(out, ensure_ascii=False, default=str))
