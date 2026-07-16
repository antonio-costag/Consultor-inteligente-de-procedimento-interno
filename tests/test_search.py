"""
Testes reais (com assert) para o modulo search.py.

Antes estes testes eram apenas impressoes em stdout em
test_semantic_search.py. Agora usam unittest.
"""

import os
import sys
import unittest

import pandas as pd

# Garante que o diretorio src/ esta no path para `import search` resolver.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import search  # noqa: E402


class SemanticSearchTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.busca = search.SemanticSearch()

    def test_dataset_carregado(self):
        self.assertTrue(self.busca.disponivel(), "Dataset deve carregar do CSV")
        self.assertGreater(self.busca.total_documentos(), 0)
        # Colunas esperadas
        for col in ['Categoria_Problema', 'Regra_POP', 'Acao_Correta_Estagiario']:
            self.assertIn(col, self.busca.df.columns)

    def test_indice_tfidf_construido(self):
        self.assertIsNotNone(self.busca.vectorizer)
        self.assertIsNotNone(self.busca.matrix)
        # matriz esparsa (n_docs, n_features)
        self.assertEqual(self.busca.matrix.shape[0], self.busca.total_documentos())

    def test_busca_termo_direto(self):
        # "impressora" aparece no dataset, a busca semantica deve achar algo
        resultados = self.busca.buscar("impressora com defeito", top_k=3)
        self.assertGreater(len(resultados), 0)
        for r in resultados:
            self.assertGreater(r['similarity'], 0.1)
            self.assertIn('Categoria_Problema', r['row'])

    def test_busca_sinonimo_encontra_resultado(self):
        # Sinonimo nao presente literal no dataset, mas a busca semantica
        # deve encontrar algo com score > 0 OU o fallback por palavra-chave
        # deve retornar resultados.
        resultados, metodo = self.busca.consulta_completa("equipamento de impressao quebrado")
        self.assertGreater(len(resultados), 0, "Esperava ao menos um resultado")
        self.assertIn(metodo, ('semantica', 'palavra_chave'))

    def test_busca_wifi(self):
        resultados, _ = self.busca.consulta_completa("senha do wifi invalida")
        self.assertGreater(len(resultados), 0)
        # Algum resultado deve mencionar wifi/EDUROAM
        achou = any(
            'wifi' in r['row']['Regra_POP'].lower() or
            'eduroam' in r['row']['Regra_POP'].lower() or
            'wifi' in r['row']['Categoria_Problema'].lower() or
            'eduroam' in r['row']['Categoria_Problema'].lower()
            for r in resultados
        )
        self.assertTrue(achou, "Esperava que algum POP mencionasse wifi/EDUROAM")

    def test_consulta_vazia(self):
        self.assertEqual(self.busca.buscar("", top_k=3), [])
        self.assertEqual(self.busca.buscar("   ", top_k=3), [])

    def test_top_k_respeitado(self):
        resultados = self.busca.buscar("problema de suporte", top_k=2)
        self.assertLessEqual(len(resultados), 2)

    def test_resultados_ordenados_por_similaridade(self):
        resultados = self.busca.buscar("impressora travando", top_k=5)
        sims = [r['similarity'] for r in resultados]
        self.assertEqual(sims, sorted(sims, reverse=True))


if __name__ == "__main__":
    unittest.main()
