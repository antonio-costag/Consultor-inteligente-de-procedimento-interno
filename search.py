"""
Modulo de busca semantica usando TF-IDF + cosine similarity.

Centraliza a logica que antes estava duplicada em main.py,
demo_semantic_search.py, demo_final.py e test_semantic_search.py.
"""

import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SemanticSearch:
    """Wrapper de busca semantica sobre o dataset de POPs."""

    SIMILARITY_THRESHOLD = 0.1

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

        documentos = [
            f"{row['Categoria_Problema']} {row['Regra_POP']} {row['Descricao_Chamado']}"
            for _, row in self.df.iterrows()
        ]
        # stop_words em ingles: o dataset e os POPs sao escritos em PT-BR,
        # mas sklearn nao tem stopwords em portugues por padrao. Mantemos
        # 'english' para cortar artigos/preposicoes que poluem o TF-IDF.
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2),
            max_features=1000,
        )
        self.matrix = self.vectorizer.fit_transform(documentos)

    def disponivel(self):
        return self.df is not None and self.matrix is not None

    def buscar(self, consulta, top_k=3):
        """Retorna ate `top_k` resultados com similaridade acima do limiar."""
        if not self.disponivel() or not consulta or not consulta.strip():
            return []

        query_vec = self.vectorizer.transform([consulta.lower()])
        sims = cosine_similarity(query_vec, self.matrix).flatten()
        top_idx = sims.argsort()[-top_k:][::-1]

        resultados = []
        for idx in top_idx:
            score = float(sims[idx])
            if score > self.SIMILARITY_THRESHOLD:
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
        palavras = consulta.lower().split()
        mask = pd.Series(False, index=self.df.index)
        for palavra in palavras:
            if len(palavra) > 3:
                mask |= self.df['Categoria_Problema'].str.lower().str.contains(palavra, na=False) | \
                        self.df['Regra_POP'].str.lower().str.contains(palavra, na=False)
        return [
            {'idx': int(i), 'similarity': None, 'row': row.to_dict()}
            for i, row in self.df[mask].head(top_k).iterrows()
        ]

    def consulta_completa(self, consulta, top_k=3):
        """Tenta busca semantica primeiro; se vazia, tenta fallback por palavra-chave."""
        resultados = self.buscar(consulta, top_k=top_k)
        if resultados:
            return resultados, 'semantica'
        return self.buscar_fallback_palavras(consulta, top_k=top_k), 'palavra_chave'

    def total_documentos(self):
        return 0 if self.df is None else len(self.df)
