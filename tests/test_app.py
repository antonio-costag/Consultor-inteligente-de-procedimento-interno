"""
Testes do servidor Flask (app.py) com foco no novo early-return de
intencoes sociais (saudacao, cortesia, despedida) e regressao do
fluxo tecnico normal.
"""

import os
import sys
import unittest
from unittest import mock

# Garante que o diretorio src/ esta no path para `import app`, `import llm`
# e `import search` resolverem a partir de la.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import app  # noqa: E402
import search  # noqa: E402


class IntencaoSocialTestCase(unittest.TestCase):
    """Testa o classificador puro, sem subir o Flask."""

    def test_saudacao_simples(self):
        self.assertEqual(app.classificar_intencao_social("oi"), "saudacao")
        self.assertEqual(app.classificar_intencao_social("Ola!"), "saudacao")
        self.assertEqual(app.classificar_intencao_social("bom dia"), "saudacao")

    def test_cortesia_simples(self):
        self.assertEqual(app.classificar_intencao_social("obrigado"), "cortesia")
        self.assertEqual(app.classificar_intencao_social("Obrigado!"), "cortesia")
        self.assertEqual(app.classificar_intencao_social("muito obrigado"), "cortesia")
        self.assertEqual(app.classificar_intencao_social("valeu"), "cortesia")

    def test_despedida_simples(self):
        self.assertEqual(app.classificar_intencao_social("tchau"), "despedida")
        self.assertEqual(app.classificar_intencao_social("Ate logo!"), "despedida")

    def test_acentos_e_pontuacao(self):
        # Acentos sao removidos na normalizacao, entao "Obrigado" -> "obrigado".
        # Pontuacao extra (!) nao muda o resultado.
        self.assertEqual(app.classificar_intencao_social("Obrigado!"), "cortesia")
        self.assertEqual(app.classificar_intencao_social("OBRIGADO"), "cortesia")
        self.assertEqual(app.classificar_intencao_social("olá!"), "saudacao")

    def test_cortesia_com_palavras_neutras(self):
        # "obrigado pela ajuda" -> "obrigado" e ancora; "pela" e "ajuda" estao
        # na whitelist. Resultado: cortesia.
        self.assertEqual(
            app.classificar_intencao_social("obrigado pela ajuda"), "cortesia"
        )
        self.assertEqual(app.classificar_intencao_social("valeu demais"), "cortesia")
        self.assertEqual(
            app.classificar_intencao_social("brigadao pela forca"), "cortesia"
        )
        self.assertEqual(app.classificar_intencao_social("obrigado amigo"), "cortesia")
        self.assertEqual(
            app.classificar_intencao_social("muito obrigado mesmo"), "cortesia"
        )

    def test_saudacao_com_palavras_neutras(self):
        self.assertEqual(app.classificar_intencao_social("oi galera"), "saudacao")
        self.assertEqual(
            app.classificar_intencao_social("bom dia meu amigo"), "saudacao"
        )

    def test_despedida_com_palavras_neutras(self):
        self.assertEqual(app.classificar_intencao_social("tchau pessoal"), "despedida")
        self.assertEqual(app.classificar_intencao_social("ate mais galera"), "despedida")

    def test_frase_mista_nao_e_cortesia(self):
        # Substantivo do dominio (vpn, impressora, wifi) quebra a cortesia,
        # mesmo se a frase comeca com palavra social.
        self.assertIsNone(app.classificar_intencao_social("obrigado, mas e a VPN?"))
        self.assertIsNone(
            app.classificar_intencao_social("valeu, mas a impressora nao funciona")
        )
        self.assertIsNone(app.classificar_intencao_social("oi, como configuro o wifi?"))

    def test_texto_vazio(self):
        self.assertIsNone(app.classificar_intencao_social(""))
        self.assertIsNone(app.classificar_intencao_social("   "))


class ApiConsultaTestCase(unittest.TestCase):
    """Testa o endpoint /api/consulta end-to-end via test_client."""

    @classmethod
    def setUpClass(cls):
        # Inicializa a base uma vez (carrega o CSV e monta o TF-IDF).
        app.inicializar()

    def setUp(self):
        self.client = app.app.test_client()

    def test_saudacao_retorna_resposta_curta(self):
        resp = self.client.post('/api/consulta', json={'duvida': 'oi'})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['metodo'], 'cortesia')
        self.assertEqual(data['resultados'], [])
        self.assertIn('mentor virtual', data['resposta'].lower())

    def test_cortesia_com_acentos_e_pontuacao(self):
        resp = self.client.post('/api/consulta', json={'duvida': 'Obrigado!'})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['metodo'], 'cortesia')
        self.assertEqual(data['resultados'], [])
        self.assertIn('Por nada', data['resposta'])

    def test_despedida_retorna_resposta_curta(self):
        resp = self.client.post('/api/consulta', json={'duvida': 'tchau'})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['metodo'], 'cortesia')
        self.assertEqual(data['resultados'], [])
        self.assertIn('Ate logo', data['resposta'])

    def test_frase_mista_cai_no_fluxo_tecnico(self):
        # Mocka a LLM para nao precisar de chave real.
        with mock.patch.object(
            app.llm, 'gerar_resposta', return_value=('resposta mock', '')
        ):
            resp = self.client.post(
                '/api/consulta', json={'duvida': 'obrigado, mas e a VPN?'}
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertNotEqual(data['metodo'], 'cortesia')
        self.assertEqual(data['resposta'], 'resposta mock')

    def test_duvida_tecnica_segue_fluxo_normal(self):
        # Regressao: o caminho real nao foi alterado.
        with mock.patch.object(
            app.llm, 'gerar_resposta', return_value=('resposta mock', '')
        ):
            resp = self.client.post(
                '/api/consulta', json={'duvida': 'minha VPN nao conecta'}
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertNotEqual(data['metodo'], 'cortesia')
        self.assertEqual(data['resposta'], 'resposta mock')

    def test_cortesia_com_palavras_neutras(self):
        # "obrigado pela ajuda" -> cortesia via match de ancora + whitelist.
        resp = self.client.post(
            '/api/consulta', json={'duvida': 'obrigado pela ajuda'}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['metodo'], 'cortesia')
        self.assertEqual(data['resultados'], [])
        self.assertIn('Por nada', data['resposta'])

    def test_duvida_vazia_retorna_400(self):
        resp = self.client.post('/api/consulta', json={'duvida': ''})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('erro', resp.get_json())


if __name__ == "__main__":
    unittest.main()
