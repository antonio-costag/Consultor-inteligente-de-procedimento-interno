"""
Testes da observabilidade minima (src/observabilidade.py).

Cobre:
- MetricsStore: cria diretorio, append, multiplas linhas, idempotencia do
  singleton, escrita concorrente.
- registrar_chamada_llm: sucesso com Response-like (objeto), sucesso com
  tupla (texto, prompt, usage_dict), erro propaga mas tambem loga.
- log_request: grava evento de /api/consulta com NaN em top_score.
- Falha de IO NAO derruba a funcao decorada.
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from unittest import mock

# Garante que `import observabilidade` resolva a partir de src/
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"),
)

import observabilidade  # noqa: E402
from observabilidade import (  # noqa: E402
    MetricsStore,
    log_request,
    registrar_chamada_llm,
)


def _isolated_store():
    """Devolve (store, path) com MetricsStore apontando para tmpdir."""
    tmp = tempfile.mkdtemp(prefix="metrics_test_")
    p = os.path.join(tmp, "sub", "llm_usage.jsonl")
    return MetricsStore(p), p, tmp


def _read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(ln) for ln in f if ln.strip()]


class MetricsStoreTestCase(unittest.TestCase):

    def setUp(self):
        # reseta o singleton para isolar testes
        MetricsStore._instance = None

    def test_cria_diretorio_e_anexa(self):
        store, path, tmp = _isolated_store()
        try:
            self.assertFalse(os.path.exists(path))
            store.log({"a": 1})
            self.assertTrue(os.path.exists(path))
            store.log({"b": 2})
            linhas = _read_lines(path)
            self.assertEqual(linhas, [{"a": 1}, {"b": 2}])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_singleton_por_processo(self):
        store, path, tmp = _isolated_store()
        try:
            MetricsStore._instance = store
            a = MetricsStore.instance()
            b = MetricsStore.instance()
            self.assertIs(a, b)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_escrita_concorrente(self):
        store, path, tmp = _isolated_store()
        try:
            def worker(i):
                for j in range(20):
                    store.log({"i": i, "j": j})
            threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            linhas = _read_lines(path)
            self.assertEqual(len(linhas), 8 * 20)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_falha_de_io_nao_propaga(self):
        store, path, tmp = _isolated_store()
        try:
            # forca OSError ao abrir o arquivo
            with mock.patch("builtins.open", side_effect=OSError("boom")):
                store.log({"x": 1})  # nao pode levantar
            self.assertFalse(os.path.exists(path))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_evento_nao_serializavel_e_ignorado(self):
        store, path, tmp = _isolated_store()
        try:
            # `object()` nao tem representacao JSON; o dump deve falhar
            # e o evento ser descartado sem criar o arquivo.
            store.log({"x": object()})
            self.assertFalse(os.path.exists(path))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class _FakeUsage:
    def __init__(self, p, c):
        self.prompt_tokens = p
        self.completion_tokens = c
        self.total_tokens = p + c


class _FakeResponse:
    def __init__(self, texto, prompt_tokens=10, completion_tokens=20, modelo="fake-1"):
        self.choices = [mock.Mock(message=mock.Mock(content=texto))]
        self.usage = _FakeUsage(prompt_tokens, completion_tokens)
        self.model = modelo


class DecoratorLLMTestCase(unittest.TestCase):

    def setUp(self):
        MetricsStore._instance = None
        self.tmp = tempfile.mkdtemp(prefix="decorator_test_")
        self.path = os.path.join(self.tmp, "llm.jsonl")
        MetricsStore._instance = MetricsStore(self.path)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_sucesso_com_objeto_response(self):
        @registrar_chamada_llm
        def gerar(duvida):
            return _FakeResponse("ok", 12, 34, "fake-1")

        resp = gerar("oi")
        self.assertEqual(resp.choices[0].message.content, "ok")
        linhas = _read_lines(self.path)
        self.assertEqual(len(linhas), 1)
        ev = linhas[0]
        self.assertEqual(ev["endpoint"], "llm")
        self.assertTrue(ev["ok"])
        self.assertEqual(ev["prompt_tokens"], 12)
        self.assertEqual(ev["completion_tokens"], 34)
        self.assertEqual(ev["total_tokens"], 46)
        self.assertEqual(ev["modelo"], "fake-1")
        self.assertGreater(ev["duracao_ms"], 0.0)

    def test_sucesso_com_tupla_usage_dict(self):
        @registrar_chamada_llm
        def gerar(duvida):
            return ("texto", "prompt", {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12})

        gerar("teste")
        linhas = _read_lines(self.path)
        self.assertEqual(len(linhas), 1)
        ev = linhas[0]
        self.assertTrue(ev["ok"])
        self.assertEqual(ev["prompt_tokens"], 5)
        self.assertEqual(ev["completion_tokens"], 7)
        self.assertEqual(ev["total_tokens"], 12)
        self.assertEqual(ev["modelo"], "")  # nao veio do response

    def test_erro_propaga_mas_tambem_loga(self):
        @registrar_chamada_llm
        def gerar(duvida):
            raise RuntimeError("groq fora do ar")

        with self.assertRaises(RuntimeError):
            gerar("x")
        linhas = _read_lines(self.path)
        self.assertEqual(len(linhas), 1)
        ev = linhas[0]
        self.assertFalse(ev["ok"])
        self.assertEqual(ev["erro"], "RuntimeError")
        self.assertEqual(ev["prompt_tokens"], 0)


class LogRequestTestCase(unittest.TestCase):

    def setUp(self):
        MetricsStore._instance = None
        self.tmp = tempfile.mkdtemp(prefix="logreq_test_")
        self.path = os.path.join(self.tmp, "llm.jsonl")
        MetricsStore._instance = MetricsStore(self.path)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_loga_evento_api_consulta(self):
        log_request(metodo="semantica", duracao_ms=42.5, top_score=0.31)
        linhas = _read_lines(self.path)
        self.assertEqual(len(linhas), 1)
        ev = linhas[0]
        self.assertEqual(ev["endpoint"], "api_consulta")
        self.assertEqual(ev["metodo"], "semantica")
        self.assertEqual(ev["duracao_ms"], 42.5)
        self.assertEqual(ev["top_score"], 0.31)
        self.assertEqual(ev["prompt_tokens"], 0)
        self.assertTrue(ev["ok"])

    def test_loga_erro(self):
        log_request(metodo="nenhum", duracao_ms=5.0, ok=False, erro="ValueError")
        linhas = _read_lines(self.path)
        self.assertEqual(len(linhas), 1)
        ev = linhas[0]
        self.assertFalse(ev["ok"])
        self.assertEqual(ev["erro"], "ValueError")

    def test_top_score_nan_vira_zero(self):
        log_request(metodo="cortesia", duracao_ms=1.0, top_score=float("nan"))
        linhas = _read_lines(self.path)
        self.assertEqual(linhas[0]["top_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
