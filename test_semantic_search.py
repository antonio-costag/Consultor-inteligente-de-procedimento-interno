import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def test_semantic_search():
    # Carregar o dataset
    df = pd.read_csv('dataset_suporte_interno_sintetico.csv.xls', sep=';', encoding='utf-8')

    print("Base de dados carregada: {} registros".format(len(df)))

    # Preparar documentos para vetorizacao
    documentos = []
    for _, row in df.iterrows():
        doc = f"{row['Categoria_Problema']} {row['Regra_POP']} {row['Descricao_Chamado']}"
        documentos.append(doc)

    # Criar vetorizador TF-IDF
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        max_features=1000
    )

    # Ajustar e transformar os documentos
    tfidf_matrix = vectorizer.fit_transform(documentos)

    print("Indice semantico criado com {} features".format(tfidf_matrix.shape[1]))

    # Testar algumas consultas
    consultas_teste = [
        "impressora nao funciona",
        "problema com impressao",
        "nao consigo imprimir documentos",
        "acesso ao wifi negado",
        "problema de senha no eduroam",
        "senha invalida para wifi"
    ]

    print("\n=== TESTE DE BUSCA SEMANTICA ===\n")

    for consulta in consultas_teste:
        print("Consulta: '{}'".format(consulta))

        # Vetorizar a consulta
        query_vector = vectorizer.transform([consulta.lower()])

        # Calcular similaridade
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()

        # Obter top 3 resultados
        top_indices = similarities.argsort()[-3:][::-1]

        print("Resultados:")
        for i, idx in enumerate(top_indices):
            similarity = similarities[idx]
            if similarity > 0.1:  # Apenas mostrar resultados com similaridade significativa
                row = df.iloc[idx]
                print("  {}. Similaridade: {:.3f}".format(i+1, similarity))
                print("     Categoria: {}".format(row['Categoria_Problema']))
                print("     Regra: {}".format(row['Regra_POP'][:80] + ("..." if len(row['Regra_POP']) > 80 else "")))
                print()

        if all(similarities[top_indices] <= 0.1):
            print("  Nenhum resultado com similaridade significativa encontrada\n")
        else:
            print()

if __name__ == "__main__":
    test_semantic_search()