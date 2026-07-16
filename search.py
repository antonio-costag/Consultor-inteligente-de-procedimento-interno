"""
Modulo de busca semantica usando TF-IDF + cosine similarity.

Centraliza a logica que antes estava duplicada em main.py,
demo_semantic_search.py, demo_final.py e test_semantic_search.py.
"""

import os
import re
import unicodedata

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _normalizar(texto):
    """Lowercase + remove acentos. 'EDUROAM' e 'Eduroam' viram o mesmo token."""
    if not texto:
        return ""
    txt = texto.lower()
    # Decompõe caracteres acentuados e remove os diacríticos
    txt = "".join(
        c for c in unicodedata.normalize("NFD", txt)
        if unicodedata.category(c) != "Mn"
    )
    # Mantém só letras, numeros e espacos
    txt = re.sub(r"[^a-z0-9\s]", " ", txt)
    # Colapsa espacos multiplos
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


class SemanticSearch:
    """Wrapper de busca semantica sobre o dataset de POPs."""

    SIMILARITY_THRESHOLD = 0.05

    def __init__(self, csv_path=None):
        if csv_path is None:
            base = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(base, 'dataset_suporte_interno_sintetico.csv.xls')
        self.csv_path = csv_path
        self.df = None
        self.vectorizer = None
        self.matrix = None
        self._carregar()

    def _carregar(self):
        try:
            self.df = pd.read_csv(self.csv_path, sep=';', encoding='utf-8')
        except FileNotFoundError:
            self.df = None
            return

        # Normaliza cada coluna antes de montar o documento, para o TF-IDF
        # receber texto limpo (sem acento, lowercase, sem pontuacao).
        documentos = [
            _normalizar(
                f"{row['Categoria_Problema']} {row['Regra_POP']} {row['Descricao_Chamado']}"
            )
            for _, row in self.df.iterrows()
        ]
        # Sem stop_words: o dataset e em PT-BR e o sklearn nao tem lista
        # em portugues por padrao. Usar 'english' apenas polui o vocabulario.
        # Bigramas ajudam em termos compostos do dominio (ex: "acesso cafe",
        # "software pirata", "visita loco").
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words=None,
            ngram_range=(1, 2),
            max_features=2000,
        )
        self.matrix = self.vectorizer.fit_transform(documentos)

    def disponivel(self):
        return self.df is not None and self.matrix is not None

    def buscar(self, consulta, top_k=3):
        """Retorna ate `top_k` resultados relevantes, sem duplicar o mesmo POP."""
        if not self.disponivel() or not consulta or not consulta.strip():
            return []

        query_norm = _normalizar(consulta)
        query_vec = self.vectorizer.transform([query_norm])
        sims = cosine_similarity(query_vec, self.matrix).flatten()

        # Ordem decrescente de score (np.argsort ascendente, [-top_k:] pega os
        # maiores no final, [::-1] inverte para o maior primeiro).
        idx_ordenado = sims.argsort()[::-1]

        resultados = []
        regras_vistas = set()  # dedup por texto da regra para evitar
                               # 3 linhas identicas do mesmo POP

        for idx in idx_ordenado:
            score = float(sims[idx])
            if score <= self.SIMILARITY_THRESHOLD:
                break  # scores ja vem em ordem decrescente, pode parar
            if len(resultados) >= top_k:
                break

            regra = self.df.iloc[idx]['Regra_POP']
            if regra in regras_vistas:
                continue
            regras_vistas.add(regra)

            resultados.append({
                'idx': int(idx),
                'similarity': score,
                'row': self.df.iloc[idx].to_dict(),
            })

        return resultados

    def buscar_fallback_palavras(self, consulta, top_k=3):
        """Fallback antigo: busca por substring caso a busca semantica nao ache nada."""
        if not self.disponivel() or not consulta:
            return []
        palavras = _normalizar(consulta).split()
        mask = pd.Series(False, index=self.df.index)
        for palavra in palavras:
            if len(palavra) > 3:
                mask |= self.df['Categoria_Problema'].apply(
                    lambda x: _normalizar(str(x)).find(palavra) >= 0
                ) | self.df['Regra_POP'].apply(
                    lambda x: _normalizar(str(x)).find(palavra) >= 0
                )
        resultados = []
        regras_vistas = set()
        for _, row in self.df[mask].iterrows():
            if row['Regra_POP'] in regras_vistas:
                continue
            regras_vistas.add(row['Regra_POP'])
            resultados.append({
                'idx': int(row.name),
                'similarity': None,
                'row': row.to_dict(),
            })
            if len(resultados) >= top_k:
                break
        return resultados

    def consulta_completa(self, consulta, top_k=3):
        """Tenta busca semantica primeiro; se vazia, tenta fallback por palavra-chave."""
        resultados = self.buscar(consulta, top_k=top_k)
        if resultados:
            return resultados, 'semantica'
        return self.buscar_fallback_palavras(consulta, top_k=top_k), 'palavra_chave'

    def total_documentos(self):
        return 0 if self.df is None else len(self.df)
