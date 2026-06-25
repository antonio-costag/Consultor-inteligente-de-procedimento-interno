"""
Demonstracao final comparando a busca antiga (palavra-chave)
com a nova busca semantica para o Consultor Inteligente
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def demonstrar_melhoria():
    print("=" * 70)
    print("DEMONSTRACAO: BUSCA POR PALAVRA-CHAVE vs BUSCA SEMANTICA")
    print("=" * 70)
    print()

    # Carregar dataset
    df = pd.read_csv('dataset_suporte_interno_sintetico.csv.xls', sep=';', encoding='utf-8')

    # Preparar documentos para vetorizacao
    documentos = []
    for _, row in df.iterrows():
        doc = f"{row['Categoria_Problema']} {row['Regra_POP']} {row['Descricao_Chamado']}"
        documentos.append(doc)

    # Criar vetorizador TF-IDF
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words='english',
        ngram_range=(1, 2),
        max_features=1000
    )

    # Ajustar e transformar
    tfidf_matrix = vectorizer.fit_transform(documentos)

    # Casos de teste que demonstram a melhoria
    casos_teste = [
        {
            'consulta': 'impressora nao funciona',
            'descricao': 'Usuario com problema de impressora'
        },
        {
            'consulta': 'nao consigo acessar o wifi',
            'descricao': 'Usuario com problema de conexao wireless'
        },
        {
            'consulta': 'senha invalida para acesso',
            'descricao': 'Usuario com problema de autenticacao'
        },
        {
            'consulta': 'computador muito lento',
            'descricao': 'Usuario reclamando de desempenho'
        }
    ]

    for caso in casos_teste:
        consulta = caso['consulta']
        descricao = caso['descricao']

        print("Cenário: {}".format(descricao))
        print("Consulta do usuario: '{}'".format(consulta))
        print("-" * 50)

        # 1. BUSCA POR PALAVRA-CHAVE (metodo antigo)
        palavras = consulta.lower().split()
        mask = pd.Series(False, index=df.index)
        for palavra in palavras:
            if len(palavra) > 3:
                mask |= df['Categoria_Problema'].str.lower().str.contains(palavra, na=False) | \
                        df['Regra_POP'].str.lower().str.contains(palavra, na=False)

        resultados_palavra_chave = df[mask]
        count_palavra_chave = len(resultados_palavra_chave)

        print("Busca por palavra-chave: {} resultado(s)".format(count_palavra_chave))
        if count_palavra_chave > 0:
            # Mostra o primeiro resultado unico
            primeiro_resultado = resultados_palavra_chave.iloc[0]
            print("  Exemplo: [{}] {}".format(
                primeiro_resultado['Categoria_Problema'],
                primeiro_resultado['Regra_POP'][:70] + "..."))
        else:
            print("  Nenhum resultado encontrado (FALHA DA BUSCA TRADICIONAL)")

        print()

        # 2. BUSCA SEMANTICA (metodo novo)
        query_vector = vectorizer.transform([consulta])
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
        top_indices = similarities.argsort()[-3:][::-1]

        # Filtra resultados com significancia estatistica
        resultados_relevantes = [(idx, similarities[idx]) for idx in top_indices if similarities[idx] > 0.1]

        print("Busca semantica: Top {} resultado(s) relevante(s)".format(len(resultados_relevantes)))
        if resultados_relevantes:
            for i, (idx, similarity) in enumerate(resultados_relevantes[:2]):  # Mostra no maximo 2
                resultado = df.iloc[idx]
                print("  {}. Similaridade: {:.3f}".format(i+1, similarity))
                print("     [{}] {}".format(
                    resultado['Categoria_Problema'],
                    resultado['Regra_POP'][:70] + "..."))
        else:
            print("  Nenhum resultado com significancia estatistica")

        print()
        print("=" * 70)
        print()

if __name__ == "__main__":
    demonstrar_melhoria()