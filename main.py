import os
import time
import random
import pandas as pd
import google.generativeai as gemini
from rich import print
from rich.panel import Panel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Configuracao do Gemini com a sua chave
gemini.configure(api_key="AIzaSyDwTCyBD-Oi0rMt1U2SkBgYq5pksLCkk4E")
model = gemini.GenerativeModel('gemini-3-flash-preview')

# SIMULACAO DE TRILHAS DE TREINAMENTO
TRILHAS_INTEGRACAO = {
    "1": {
        "titulo": "Primeiro Dia: Configuracao do Ambiente de Desenvolvimento",
        "passos": [
            "1. Solicite suas credenciais temporarias no portal de acessos.",
            "2. Instale a VPN corporativa seguindo o script de automatizacao no repositorio inicial.",
            "3. Clone o repositorio principal da empresa e instale as dependencias (rode 'make install').",
            "4. Verifique se o ambiente subiu localmente na porta 8080."
        ],
        "concluido": False
    },
    "2": {
        "titulo": "Atendimento de Suporte: Triagem de Chamados",
        "passos": [
            "1. Ao receber um ticket, verifique a severidade (P1, P2 ou P3).",
            "2. Tickets P1 (Sistemas fora do ar) devem ser escalados imediatamente para o Senor plantonista.",
            "3. Tickets P2 e P3: tente reproduzir o erro no seu ambiente local primeiro.",
            "4. Documente os passos de reproducao na aba 'Comentarios Internos' do Jira."
        ],
        "concluido": False
    }
}

dataset_chamados = None
tfidf_vectorizer = None
tfidf_matrix = None

def inicializar_busca_semantica():
    """Inicializa o vetorizador TF-IDF e cria a matriz de documentos para busca semantica."""
    global tfidf_vectorizer, tfidf_matrix, dataset_chamados

    if dataset_chamados is None or dataset_chamados.empty:
        return

    # Combinar colunas relevantes para busca semantica
    # Usamos Categoria_Problema, Regra_POP e Descricao_Chamado para melhor contexto
    documentos = []
    for _, row in dataset_chamados.iterrows():
        # Combinar múltiplos campos para criar um documento rico
        doc = f"{row['Categoria_Problema']} {row['Regra_POP']} {row['Descricao_Chamado']}"
        documentos.append(doc)

    # Criar e ajustar o vetorizador TF-IDF
    tfidf_vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words='english',  # Usando english como fallback para evitar problemas de idioma
        ngram_range=(1, 2),
        max_features=1000
    )

    # Ajustar e transformar os documentos
    tfidf_matrix = tfidf_vectorizer.fit_transform(documentos)

def carregar_dataset():
    """Funcao para carregar o dataset sintético na inicializacao."""
    global dataset_chamados

    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(diretorio_atual, 'dataset_suporte_interno_sintetico.csv.xls')

    try:
        dataset_chamados = pd.read_csv(caminho_arquivo, sep=';', encoding='utf-8')
        print("[OK] Base de conhecimento carregada: {} POPs indexados.".format(len(dataset_chamados)))
        time.sleep(1.5)

        # Inicializar o indice semantico apos carregar os dados
        inicializar_busca_semantica()

    except Exception as e:
        print("[AVISO] Erro ao carregar o dataset '{}': {}".format(caminho_arquivo, e))
        print("[AVISO] O sistema rodará em modo de demonstracao restrito (sem os dados).")
        time.sleep(2)
        dataset_chamados = None

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def cabecalho():
    limpar_tela()
    print("=" * 65)
    print(" ONBOARDING INTELIGENTE: SEU MENTOR VIRTUAL DE TREINAMENTO ")
    print("=" * 65)

def iniciar_trilha():
    while True:
        cabecalho()
        print("--- TRILHAS DE TREINAMENTO DISPONIVEIS ---\n")

        for chave, trilha in TRILHAS_INTEGRACAO.items():
            status = "[CONCLUIDO]" if trilha["concluido"] else "[EM PROGRESSO]"
            print(" [{}] {} {}".format(chave, status, trilha['titulo']))

        print(" [0] Voltar ao menu principal")

        opcao = input("\nQual treinamento você deseja iniciar? ")

        if opcao == '0':
            break
        elif opcao in TRILHAS_INTEGRACAO:
            executar_treinamento(opcao)
        else:
            print("[ERRO] Opcao invalida.")
            time.sleep(1)

def executar_treinamento(id_trilha):
    trilha = TRILHAS_INTEGRACAO[id_trilha]
    cabecalho()
    print("--- {} ---\n".format(trilha['titulo']))
    print("Vamos passar por este processo passo a passo.\n")

    for passo in trilha['passos']:
        print(passo)
        input(" > Pressione ENTER para confirmar o entendimento e avançar...")

    print("\n[SUCESSO] Excelente! Você concluiu esta trilha de conhecimento.")
    trilha['concluido'] = True
    input("Pressione ENTER para retornar às trilhas...")

def simular_tarefa():
    cabecalho()
    print("--- SIMULADOR DE TAREFAS (AMBIENTE SEGURO) ---\n")

    global dataset_chamados

    if dataset_chamados is None or dataset_chamados.empty:
        print("Vamos testar seus conhecimentos. Cenário:")
        print("Um cliente abriu um ticket dizendo que o sistema principal caiu e está fora do ar.\n")
        print("O que você faz?")
        print(" [A] Tento descobrir o erro lendo os logs locais.")
        print(" [B] Classifico como P1 e escalo para o Sênior plantonista.")
        print(" [C] Fecho o ticket e peço mais informações ao cliente.")

        resposta = input("\nSua ação (A/B/C): ").upper()
        if resposta == 'B':
            print("\n[CORRETO] Correto! Regra de ouro do treinamento de Suporte: P1 escala na hora.")
        else:
            print("\n[ERRO] Cuidado! Segundo nosso POP de Suporte, quedas de sistema são nível P1.")

        input("\nPressione ENTER para voltar...")
        return

    print("Vamos testar seus conhecimentos com um cenário gerado a partir do histórico:\n")

    ticket = dataset_chamados.sample(1).iloc[0]

    print("🎫 [TICKET]: {}".format(ticket['Ticket_ID']))
    print("🏢 [DEPARTAMENTO]: {}".format(ticket['Departamento']))
    print("🎭 [HUMOR DO USUÁRIO]: {}".format(ticket['Humor_Usuario']))
    print("⚠️ [CATEGORIA]: {}".format(ticket['Categoria_Problema']))
    print("📝 [DESCRIÇÃO]: \"{}\"\n".format(ticket['Descricao_Chamado']))

    print("O que você faz como suporte/estagiário?")

    acao_correta = ticket['Acao_Correta_Estagiario']

    acoes_erradas = dataset_chamados[
        dataset_chamados['Acao_Correta_Estagiario'] != acao_correta
    ]['Acao_Correta_Estagiario'].drop_duplicates().sample(2).tolist()

    opcoes = [acao_correta] + acoes_erradas
    random.shuffle(opcoes)

    letras = ['A', 'B', 'C']
    letra_correta = ''

    for i in range(3):
        if opcoes[i] == acao_correta:
            letra_correta = letras[i]
        print(" [{}] {}".format(letras[i], opcoes[i]))

    resposta = input("\nSua ação (A/B/C): ").upper()

    if resposta == letra_correta:
        print("\n[CORRETO] Correto! Você seguiu o procedimento adequado.")
    else:
        print("\n[ERRO] Incorreto. A opção certa seria a [{}].".format(letra_correta))

    print("[DICA] Regra POP de Feedback: {}".format(ticket['Regra_POP']))

    input("\nPressione ENTER para voltar...")

def consulta_livre_semantica(duvida, top_k=3):
    """Realiza busca semantica usando TF-IDF e similaridade de cosseno."""
    global dataset_chamados, tfidf_vectorizer, tfidf_matrix

    if dataset_chamados is None or dataset_chamados.empty or tfidf_vectorizer is None or tfidf_matrix is None:
        return []

    # Vetorizar a consulta do usuário
    query_vector = tfidf_vectorizer.transform([duvida.lower()])

    # Calcular similaridade de cosseno entre a consulta e todos os documentos
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()

    # Obter os índices dos top_k documentos mais similares
    top_indices = similarities.argsort()[-top_k:][::-1]

    # Filtrar apenas resultados com similaridade acima de um limiar mínimo
    resultados = []
    for idx in top_indices:
        if similarities[idx] > 0.1:  # Limiar mínimo de similaridade
            resultados.append({
                'idx': idx,
                'similarity': similarities[idx],
                'row': dataset_chamados.iloc[idx]
            })

    return resultados

def consulta_livre():
    cabecalho()
    print("--- CONSULTA AO MENTOR VIRTUAL ---")
    print("Travou em alguma tarefa? Descreva o problema que você está enfrentando.")

    print("\n[SUA DUVIDA]: ", end='')
    duvida = input().lower()

    print("\n[PROCESSANDO] O Mentor está analisando os manuais da empresa e gerando uma resposta...")

    global dataset_chamados
    fatos = ""

    # 1. Recuperação (Retrieval): Busca semantica relacionada no dataset
    if dataset_chamados is not None and not dataset_chamados.empty:
        resultados = consulta_livre_semantica(duvida, top_k=3)

        if resultados:
            for resultado in resultados:
                linha = resultado['row']
                similaridade = resultado['similarity']
                fatos += "- Categoria: {} | Regra: {} | Ação Recomendada: {} (Similaridade: {:.2f})\n".format(
                    linha['Categoria_Problema'], linha['Regra_POP'], linha['Acao_Correta_Estagiario'], similaridade)
        else:
            # Se nenhum resultado atingir o limiar de similaridade, fallback para busca por palavras-chave
            palavras = duvida.split()
            mask = pd.Series(False, index=dataset_chamados.index)
            for palavra in palavras:
                if len(palavra) > 3:
                    mask |= dataset_chamados['Categoria_Problema'].str.lower().str.contains(palavra, na=False) | \
                            dataset_chamados['Regra_POP'].str.lower().str.contains(palavra, na=False)

            resultados = dataset_chamados[mask]

            if not resultados.empty:
                for _, linha in resultados.head(3).iterrows():
                    fatos += "- Categoria: {} | Regra: {} | Ação Recomendada: {}\n".format(
                        linha['Categoria_Problema'], linha['Regra_POP'], linha['Acao_Correta_Estagiario'])
            else:
                fatos = "- Nenhum procedimento específico encontrado na base local. Aja com base no bom senso corporativo ou direcione ao Sênior."
    else:
        fatos = "- Nenhum procedimento específico encontrado na base local. Aja com base no bom senso corporativo ou direcione ao Sênior."

    # 2. Aumento de Contexto (Augmentation): Cria o prompt injetando as regras
    prompt = """Você é um Consultor Inteligente de Procedimentos Internos ajudando um estagiário de suporte de TI.
Responda à dúvida do estagiário de forma direta, clara e profissional.

Regra Fundamental: BASEIE SUA RESPOSTA EXCLUSIVAMENTE NOS PROCEDIMENTOS ABAIXO. Se a solução não estiver nos procedimentos, instrua o estagiário a escalar o ticket para um analista Sênior.

PROCEDIMENTOS INTERNOS RECUPERADOS:
{fatos}

DÚVIDA DO ESTAGIÁRIO:
"{duvida}"
""".format(fatos=fatos, duvida=duvida)

    print("\n[DEBUG] O que o Gemini está recebendo ---")
    print(prompt)
    print("---------------------------------------------")
    input("\nPressione ENTER para ver a resposta da IA...")

    # 3. Geração (Generation): Chama a API do Gemini e formata com a biblioteca 'rich'
    try:
        response = model.generate_content(prompt)
        resposta_text = "[WHITE]" + response.text + "[/]"

        caixa = Panel(resposta_text, title="Mentor IA :star:", style="white", width=100)
        print("\n")
        print(caixa)

    except Exception as e:
        print("\n[ERRO] Ocorreu um erro na comunicação com o Gemini:\n{}[/]".format(e))

    input("\nPressione ENTER para voltar...")

def menu_principal():
    while True:
        cabecalho()
        print("Bem-vindo(a) ao seu primeiro dia! O que faremos agora?\n")

        print(" [1] Trilhas de Treinamento")
        print(" [2] Simulador de Tarefas")
        print(" [3] Consulta Livre ao Mentor Virtual")
        print(" [0] Sair")

        opcao = input("\nEscolha uma opção: ")

        if opcao == '0':
            print("\n[ATE LOGO] Obrigado por usar o Consultor Inteligente de Procedimentos Internos!")
            break
        elif opcao == '1':
            iniciar_trilha()
        elif opcao == '2':
            simular_tarefa()
        elif opcao == '3':
            consulta_livre()
        else:
            print("[ERRO] Opção inválida.")
            time.sleep(1)

# Inicialização do programa
if __name__ == "__main__":
    carregar_dataset()
    menu_principal()