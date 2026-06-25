import os
import time

# SIMULAÇÃO DE TRILHAS DE TREINAMENTO
TRILHAS_INTEGRACAO = {
    "1": {
        "titulo": "Primeiro Dia: Configuração do Ambiente de Desenvolvimento",
        "passos": [
            "1. Solicite suas credenciais temporárias no portal de acessos.",
            "2. Instale a VPN corporativa seguindo o script de automação no repositório inicial.",
            "3. Clone o repositório principal da empresa e instale as dependências (rode 'make install').",
            "4. Verifique se o ambiente subiu localmente na porta 8080."
        ],
        "concluido": False
    },
    "2": {
        "titulo": "Atendimento de Suporte: Triagem de Chamados",
        "passos": [
            "1. Ao receber um ticket, verifique a severidade (P1, P2 ou P3).",
            "2. Tickets P1 (Sistemas fora do ar) devem ser escalados imediatamente para o Sênior plantonista.",
            "3. Tickets P2 e P3: tente reproduzir o erro no seu ambiente local primeiro.",
            "4. Documente os passos de reprodução na aba 'Comentários Internos' do Jira."
        ],
        "concluido": False
    }
}

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def cabecalho():
    limpar_tela()
    print("=" * 65)
    print(" 🎓 ONBOARDING INTELIGENTE: SEU MENTOR VIRTUAL DE TREINAMENTO")
    print("=" * 65)

def iniciar_trilha():
    while True:
        cabecalho()
        print("--- 🛤️ Trilhas de Treinamento Disponíveis ---\n")
        
        for chave, trilha in TRILHAS_INTEGRACAO.items():
            status = "✅" if trilha["concluido"] else "⏳"
            print(f" [{chave}] {status} {trilha['titulo']}")
            
        print(" [0] Voltar ao menu principal")
        
        opcao = input("\nQual treinamento você deseja iniciar? ")
        
        if opcao == '0':
            break
        elif opcao in TRILHAS_INTEGRACAO:
            executar_treinamento(opcao)
        else:
            print("Opção inválida.")
            time.sleep(1)

def executar_treinamento(id_trilha):
    trilha = TRILHAS_INTEGRACAO[id_trilha]
    cabecalho()
    print(f"--- 📚 {trilha['titulo']} ---\n")
    print("Vamos passar por este processo passo a passo.\n")
    
    for passo in trilha['passos']:
        print(passo)
        input(" > Pressione ENTER para confirmar o entendimento e avançar...")
    
    print("\n🎉 Excelente! Você concluiu esta trilha de conhecimento.")
    trilha['concluido'] = True
    input("Pressione ENTER para retornar às trilhas...")

def simular_tarefa():
    cabecalho()
    print("--- 🛠️ Simulador de Tarefas (Ambiente Seguro) ---\n")
    print("Vamos testar seus conhecimentos. Cenário:")
    print("Um cliente abriu um ticket dizendo que o sistema principal caiu e está fora do ar.\n")
    
    print("O que você faz?")
    print(" [A] Tento descobrir o erro lendo os logs locais.")
    print(" [B] Classifico como P1 e escalo para o Sênior plantonista.")
    print(" [C] Fecho o ticket e peço mais informações ao cliente.")
    
    resposta = input("\nSua ação (A/B/C): ").upper()
    
    if resposta == 'B':
        print("\n✅ Correto! Regra de ouro do treinamento de Suporte: P1 escala na hora.")
    else:
        print("\n❌ Cuidado! Segundo nosso POP de Suporte, quedas de sistema são nível P1 e devem ser escaladas imediatamente para o Sênior.")
        
    input("\nPressione ENTER para voltar...")

def consulta_livre():
    cabecalho()
    print("--- 🙋 Consulta ao Mentor Virtual ---")
    print("Travou em alguma tarefa? Me explique o que está tentando fazer.")
    duvida = input("\nSua dúvida: ")
    print("\nProcessando nos manuais internos...")
    time.sleep(1.5)
    print("\n💡 Dica do Mentor: Pelo que você descreveu, recomendo revisar a Trilha de Treinamento 1 (Configuração de Ambiente).")
    input("\nPressione ENTER para voltar...")

def menu_principal():
    while True:
        cabecalho()
        print("Bem-vindo(a) ao seu primeiro dia! O que faremos agora?\n")
        print(" [1] 🛤️  Iniciar Trilhas de Treinamento Guiado")
        print(" [2] 🛠️  Modo Simulação (Praticar Tarefas)")
        print(" [3] 🙋 Tirar dúvida específica sobre um procedimento")
        print(" [4] ❌ Encerrar expediente")

        opcao = input("\nEscolha sua próxima atividade (1-4): ")

        if opcao == '1':
            iniciar_trilha()
        elif opcao == '2':
            simular_tarefa()
        elif opcao == '3':
            consulta_livre()
        elif opcao == '4':
            print("\nAté amanhã! Lembre-se que o treinamento é contínuo.\n")
            break
        else:
            print("\nOpção inválida.")
            time.sleep(1)

if __name__ == "__main__":
    menu_principal()