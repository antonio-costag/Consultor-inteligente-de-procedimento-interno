"""
Menu CLI do Consultor Inteligente de Procedimentos Internos.

Carrega a base, mostra as opcoes de treinamento, simulacao e consulta livre.
A consulta livre usa busca semantica (search.py) + Gemini (llm.py).
"""

import os
import time
import random

from rich import print
from rich.panel import Panel

import llm
import search as search_mod


# Trilhas de treinamento (simuladas)
TRILHAS_INTEGRACAO = {
    "1": {
        "titulo": "Primeiro Dia: Configuracao do Ambiente de Desenvolvimento",
        "passos": [
            "1. Solicite suas credenciais temporarias no portal de acessos.",
            "2. Instale a VPN corporativa seguindo o script de automatizacao no repositorio inicial.",
            "3. Clone o repositorio principal da empresa e instale as dependencias (rode 'make install').",
            "4. Verifique se o ambiente subiu localmente na porta 8080.",
        ],
        "concluido": False,
    },
    "2": {
        "titulo": "Atendimento de Suporte: Triagem de Chamados",
        "passos": [
            "1. Ao receber um ticket, verifique a severidade (P1, P2 ou P3).",
            "2. Tickets P1 (Sistemas fora do ar) devem ser escalados imediatamente para o Senior plantonista.",
            "3. Tickets P2 e P3: tente reproduzir o erro no seu ambiente local primeiro.",
            "4. Documente os passos de reproducao na aba 'Comentarios Internos' do Jira.",
        ],
        "concluido": False,
    },
}


# Estado global da busca semantica (carregado uma vez no startup)
busca: search_mod.SemanticSearch | None = None


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
            print(f" [{chave}] {status} {trilha['titulo']}")
        print(" [0] Voltar ao menu principal")

        opcao = input("\nQual treinamento voce deseja iniciar? ")
        if opcao == '0':
            break
        if opcao in TRILHAS_INTEGRACAO:
            executar_treinamento(opcao)
        else:
            print("[ERRO] Opcao invalida.")
            time.sleep(1)


def executar_treinamento(id_trilha):
    trilha = TRILHAS_INTEGRACAO[id_trilha]
    cabecalho()
    print(f"--- {trilha['titulo']} ---\n")
    print("Vamos passar por este processo passo a passo.\n")
    for passo in trilha['passos']:
        print(passo)
        input(" > Pressione ENTER para confirmar o entendimento e avancar...")
    print("\n[SUCESSO] Excelente! Voce concluiu esta trilha de conhecimento.")
    trilha['concluido'] = True
    input("Pressione ENTER para retornar as trilhas...")


def simular_tarefa():
    cabecalho()
    print("--- SIMULADOR DE TAREFAS (AMBIENTE SEGURO) ---\n")

    if not busca or not busca.disponivel():
        print("Base de dados nao carregada. Cenario generico:\n")
        print("Um cliente abriu um ticket dizendo que o sistema principal caiu e esta fora do ar.\n")
        print("O que voce faz?")
        print(" [A] Tento descobrir o erro lendo os logs locais.")
        print(" [B] Classifico como P1 e escalo para o Senior plantonista.")
        print(" [C] Fecho o ticket e peco mais informacoes ao cliente.")
        resposta = input("\nSua acao (A/B/C): ").upper()
        if resposta == 'B':
            print("\n[CORRETO] Correto! Regra de ouro do treinamento de Suporte: P1 escala na hora.")
        else:
            print("\n[ERRO] Cuidado! Segundo nosso POP de Suporte, quedas de sistema sao nivel P1.")
        input("\nPressione ENTER para voltar...")
        return

    print("Vamos testar seus conhecimentos com um cenario gerado a partir do historico:\n")
    ticket = busca.df.sample(1).iloc[0]
    print(f" [TICKET]: {ticket['Ticket_ID']}")
    print(f" [DEPARTAMENTO]: {ticket['Departamento']}")
    print(f" [HUMOR DO USUARIO]: {ticket['Humor_Usuario']}")
    print(f" [CATEGORIA]: {ticket['Categoria_Problema']}")
    print(f" [DESCRICAO]: \"{ticket['Descricao_Chamado']}\"\n")
    print("O que voce faz como suporte/estagiario?")

    acao_correta = ticket['Acao_Correta_Estagiario']
    acoes_erradas = busca.df[
        busca.df['Acao_Correta_Estagiario'] != acao_correta
    ]['Acao_Correta_Estagiario'].drop_duplicates().sample(2).tolist()
    opcoes = [acao_correta] + acoes_erradas
    random.shuffle(opcoes)

    letras = ['A', 'B', 'C']
    letra_correta = ''
    for i in range(3):
        if opcoes[i] == acao_correta:
            letra_correta = letras[i]
        print(f" [{letras[i]}] {opcoes[i]}")

    resposta = input("\nSua acao (A/B/C): ").upper()
    if resposta == letra_correta:
        print("\n[CORRETO] Correto! Voce seguiu o procedimento adequado.")
    else:
        print(f"\n[ERRO] Incorreto. A opcao certa seria a [{letra_correta}].")
    print(f"[DICA] Regra POP de Feedback: {ticket['Regra_POP']}")
    input("\nPressione ENTER para voltar...")


def consulta_livre():
    cabecalho()
    print("--- CONSULTA AO MENTOR VIRTUAL ---")
    print("Travou em alguma tarefa? Descreva o problema que voce esta enfrentando.\n")
    duvida = input("[SUA DUVIDA]: ")
    print("\n[PROCESSANDO] O Mentor esta analisando os manuais da empresa...")

    resultados, metodo = busca.consulta_completa(duvida, top_k=3)
    if metodo == 'semantica':
        print(f"[INFO] {len(resultados)} procedimentos relevantes via busca semantica.")
    elif resultados:
        print(f"[INFO] {len(resultados)} procedimentos via busca por palavra-chave (fallback).")
    else:
        print("[INFO] Nenhum procedimento encontrado na base local.")

    try:
        resposta, _prompt = llm.gerar_resposta(duvida, resultados, top_k=3)
        caixa = Panel(resposta, title="Mentor IA", style="white", width=100)
        print("\n")
        print(caixa)
    except Exception as e:
        print(f"\n[ERRO] Ocorreu um erro na comunicacao com o Gemini:\n{e}")

    input("\nPressione ENTER para voltar...")


def menu_principal():
    while True:
        cabecalho()
        print("Bem-vindo(a) ao seu primeiro dia! O que faremos agora?\n")
        print(" [1] Trilhas de Treinamento")
        print(" [2] Simulador de Tarefas")
        print(" [3] Consulta Livre ao Mentor Virtual")
        print(" [0] Sair")

        opcao = input("\nEscolha uma opcao: ")
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
            print("[ERRO] Opcao invalida.")
            time.sleep(1)


def inicializar():
    global busca
    busca = search_mod.SemanticSearch()
    llm.configurar()
    if busca.disponivel():
        print(f"[OK] Base de conhecimento carregada: {busca.total_documentos()} POPs indexados.")
    else:
        print("[AVISO] Dataset nao encontrado. Sistema rodara em modo restrito.")


if __name__ == "__main__":
    inicializar()
    time.sleep(1.5)
    menu_principal()
