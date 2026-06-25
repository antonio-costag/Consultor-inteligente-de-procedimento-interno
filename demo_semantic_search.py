"""
Demonstracao da diferença entre busca por palavra-chave e busca semantica
para o Consultor Inteligente de Procedimentos Internos
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def demonstrar_busca_semantica():
    # Carregar o dataset (mesmo código do main.py)
    df = pd.read_csv('dataset_suporte_interno_sintetico.csv.xls', sep=';', encoding='utf-8')

    print("=== DEMONSTRACAO: BUSCA POR PALAVRA-CHAVE vs BUSCA SEMANTICA ===\n")

    # Mostrar alguns exemplos do dataset
    print("Exemplos de procedimentos no banco de dados:")
    for i in range(min(3, len(df))):
        row = df.iloc[i]
        print(f"{i+1}. [{row['Categoria_Problema']}] {row['Regra_POP']}")
    print()

    # Preparar documentos para vetorizacao (mesmo processo do main.py)
    documentos = []
    for _, row in df.iterrows():
        doc = f"{row['Categoria_Problema']} {row['Regra_POP']} {row['Descricao_Chamado']}"
        documentos.append(doc)

    # Criar vetorizador TF-IDF (sem stop words para evitar problemas de idioma)
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        max_features=1000
    )

    # Ajustar e transformar os documentos
    tfidf_matrix = vectorizer.fit_transform(documentos)

    # Exemplos de consultas para testar
    consultas_teste = [
        "impressora nao funciona",
        "problema com impressao",
        "equipamento de impressao quebrado",
        "nao consigo imprimir documentos",
        "acesso ao wifi negado",
        "problema de senha no eduroam",
        "senha invalida para wifi"
    ]

    print("Comparando resultados:\n")

    for consulta in consultas_teste:
        print(f"Consulta: '{consulta}'")
        print("-" * 50)

        # 1. BUSCA POR PALAVRA-CHAVE (metodo antigo)
        palavras = consulta.lower().split()
        mask = pd.Series(False, index=df.index)
        for palavra in palavras:
            if len(palavra) > 3:  # Mesmo filtro do codigo original
                mask |= df['Categoria_Problema'].str.lower().str.contains(palavra, na=False) | \
                        df['Regra_POP'].str.lower().str.contains(palavra, na=False)

        resultados_palavra_chave = df[mask]
        print(f"Busca por palavra-chave: {len(resultados_palavra_chave)} resultados")
        if len(resultados_palavra_chave) > 0:
            for idx, row in resultados_palavra_chave.head(2).iterrows():
                print(f"  -> [{row['Categoria_Problema']}] {row['Regra_POP'][:60]}...")
        else:
            print("  -> Nenhum resultado encontrado")

        print()

        # 2. BUSCA SEMANTICA (metodo novo)
        query_vector = vectorizer.transform([consulta])
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
        top_indices = similarities.argsort()[-3:][::-1]  # Top 3 mais similares

        resultados_semanticos = df.iloc[top_indices]
        print(f"Busca semantica: Top 3 resultados (similarity > 0.1)")
        for i, idx in enumerate(top_indices):
            similarity = similarities[idx]
            if similarity > 0.1:  # Apenas mostrar se houver similaridade significativa
                row = df.iloc[idx]
                print(f"  {i+1}. Similaridade: {similarity:.3f}")
                print(f"     [{row['Categoria_Problema']}] {row['Regra_POP'][:60]}...")

        if all(similarities[top_indices] <= 0.1):
            print("  -> Nenhum resultado com similaridade significativa")

        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    demonstrar_busca_semantica()