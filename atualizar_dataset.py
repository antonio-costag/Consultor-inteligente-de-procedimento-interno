"""
Reescreve o dataset com POPs mais operacionais.

O dataset original tem 1 regra unica repetida N vezes por categoria (ex: 109
linhas de CAFe/EDUROAM com a mesma frase). Isso prejudica a busca semantica
e confunde o LLM (POPs vagos -> LLM "escala" em vez de responder).

Aqui geramos 5 variacoes de regra + acao por categoria e distribuimos entre
as linhas existentes, mantendo Ticket_ID, Departamento, Humor, Descricao.
Rodar uma unica vez: python atualizar_dataset.py
"""

import pandas as pd

ARQ = "dataset_suporte_interno_sintetico.csv.xls"

# 5 variacoes de (regra, acao) por categoria. Textos pensados para serem
# operacionais (passo a passo claro) e em PT-BR sem dependencia de acento.
POPs = {
    "Acesso CAFe / EDUROAM": [
        (
            "Quando o usuario relatar erro de senha no EDUROAM ou CAFe: "
            "1) Acesse o SIGU/SIG com o login institucional. "
            "2) Verifique se o cadastro foi atualizado nos ultimos 3 dias uteis. "
            "3) Se foi, oriente a aguardar o prazo de migracao. "
            "4) Se nao foi, encaminhe o usuario a PROGEP/DERCA para atualizacao cadastral.",
            "Confirmar com o usuario a data da ultima atualizacao no SIGU/SIG. "
            "Se foi ha menos de 3 dias uteis, orientar que aguarde. "
            "Se foi ha mais de 3 dias uteis, abrir chamado para a equipe de redes.",
        ),
        (
            "Para problemas de login no EDUROAM (credenciais invalidas, "
            "conta bloqueada, autenticacao falhando): "
            "1) Verifique se o usuario esta usando o login completo (usuario@dominio). "
            "2) Confirme se a senha foi alterada recentemente. "
            "3) Oriente reset de senha pelo SIGU. "
            "4) Se persistir, escale para a equipe de redes.",
            "Solicitar ao usuario o login institucional completo. "
            "Pedir print do erro de autenticacao. "
            "Orientar reset de senha pelo portal do SIGU antes de escalar.",
        ),
        (
            "Quando o usuario nao consegue acessar o portal de periodicos "
            "Capes via CAFe: verifique vinculo institucional ativo no SIGU. "
            "Se o vinculo constar como expirado, encaminhar para PROGEP/DERCA. "
            "Apos atualizacao, prazo de migracao de 3 dias uteis.",
            "Pedir CPF e login institucional. "
            "Consultar status do vinculo no SIGU. "
            "Se expirado, orientar o usuario a procurar a PROGEP/DERCA.",
        ),
        (
            "Para usuarios que reportam EDUROAM conectando mas sem acesso a "
            "internet: verificar se o certificado de seguranca esta instalado. "
            "Se nao estiver, orientar a instalacao do CAT (Configuration "
            "Assistant Tool) do EDUROAM. Se certificado ok, escalar para redes.",
            "Confirmar se e problema de autenticacao (nao conecta) ou de "
            "conectividade (conecta mas nao navega). "
            "No segundo caso, instalar/atualizar o certificado EDUROAM.",
        ),
        (
            "Quando o problema de acesso CAFe/EDUROAM for reincidente: "
            "abrir chamado priorizando historico do usuario. "
            "Verificar se ha troca de vinculo institucional (graduacao para "
            "pos, por exemplo). Migracao entre vinculos exige atualizacao "
            "no SIGU e prazo de 3 dias uteis.",
            "Consultar historico de chamados do usuario. "
            "Identificar se houve mudanca de vinculo recente. "
            "Documentar no ticket o passo a passo feito antes de escalar.",
        ),
    ],
    "Software Pirata": [
        (
            "E proibida a instalacao ou manutencao de software sem licenca "
            "valida. Se o usuario pedir instalacao de software pirateado "
            "(Windows, Office, Photoshop etc): "
            "1) Recusar educadamente. "
            "2) Informar que a instituicao oferece alternativas licenciadas. "
            "3) Documentar a solicitacao no ticket.",
            "Recusar a instalacao. "
            "Listar alternativas gratuitas ou licenciadas disponiveis na instituicao. "
            "Registrar a solicitacao indevida no ticket.",
        ),
        (
            "Quando o usuario relatar problema com software nao licenciado "
            "(travamentos, expiracao, malware): "
            "1) Recomendar desinstalacao. "
            "2) Instalar alternativa licenciada disponivel. "
            "3) Alertar sobre riscos de seguranca e compliance.",
            "Orientar a desinstalacao do software irregular. "
            "Instalar a versao licenciada institucional ou alternativa free. "
            "Registrar a ocorrencia para fins de auditoria de TI.",
        ),
        (
            "Solicitacoes de 'crack', 'ativador', 'keygen' ou instalacao "
            "de software pago sem licenca: recusar categoricamente. "
            "Redirecionar para a coordenacao de TI verificar alternativas "
            "licenciadas ou versoes gratuitas oficiais.",
            "Recusar a solicitacao. "
            "Nao instalar nenhum software de origem duvidosa. "
            "Reportar a solicitacao a coordenacao de TI.",
        ),
        (
            "Para problemas com Office/Windows pirata em maquinas da "
            "instituicao: agendar remocao e instalacao da versao "
            "institucional licenciada. Em maquinas de uso pessoal, orientar "
            "o usuario a buscar suporte externo.",
            "Em equipamento institucional: agendar formatacao/reinstalacao. "
            "Em equipamento pessoal: informar que nao ha suporte para software pirata.",
        ),
        (
            "Quando o usuario ja tem software pirata instalado e a maquina "
            "apresenta problemas: o suporte pode ajudar a desinstalar e "
            "instalar versao licenciada. Nao ha suporte para manter o "
            "software irregular funcionando.",
            "Desinstalar o software irregular. "
            "Instalar alternativa licenciada. "
            "Documentar todo o processo no ticket.",
        ),
    ],
    "Equipamento Inservivel": [
        (
            "Equipamento obsoleto ou sem viabilidade de conserto deve "
            "receber laudo de baixa patrimonial. "
            "1) Preencher o formulario de baixa. "
            "2) Coletar numero de patrimonio e estado do equipamento. "
            "3) Encaminhar para o setor de patrimonio.",
            "Avaliar o estado do equipamento. "
            "Se sem conserto viavel, preencher laudo de baixa. "
            "Encaminhar para o setor de patrimonio responsavel.",
        ),
        (
            "Para equipamentos com defeito sem reparo viavel (queimado, "
            "componente indisponivel, custo de reparo maior que o valor "
            "do equipamento): abrir processo de baixa patrimonial. "
            "Substituir por equipamento do estoque se disponivel.",
            "Documentar o defeito com fotos e descricao tecnica. "
            "Verificar estoque de equipamentos reserva. "
            "Acionar patrimonio para baixa do item.",
        ),
        (
            "Computadores muito antigos que nao rodam sistemas modernos: "
            "avaliar uso atual. Se o usuario precisa de um software novo, "
            "substituir a maquina. Se o uso e basico, manter ate a baixa "
            "natural e realocar o usuario.",
            "Identificar as necessidades do usuario. "
            "Comparar com a capacidade da maquina. "
            "Propor substituicao ou manutencao conforme o caso.",
        ),
        (
            "Equipamento com danos fisicos graves (queda, liquido, "
            "superaquecimento): nao ha reparo. "
            "Iniciar processo de baixa imediatamente. "
            "Se for equipamento emprestado, documentar a condicao com o usuario.",
            "Fotografar os danos. "
            "Solicitar baixa patrimonial. "
            "Notificar o usuario em caso de equipamento emprestado.",
        ),
        (
            "Quando o equipamento apresenta defeito intermitente que "
            "impossibilita o trabalho: substituir preventivamente. "
            "Abrir chamado de baixa preventiva enquanto o equipamento "
            "reserva e instalado, evitando perda de produtividade.",
            "Trocar pelo equipamento reserva. "
            "Encaminhar o defeituoso para analise tecnica. "
            "Se nao houver reparo, abrir baixa patrimonial.",
        ),
    ],
    "Visita in Loco": [
        (
            "Maximo de 2 tentativas de visita fisica por chamado. "
            "Transporte de equipamento a oficina e responsabilidade do "
            "usuario. "
            "1) Confirmar presenca do usuario antes de ir. "
            "2) Documentar cada tentativa no ticket. "
            "3) Apos 2 tentativas sem sucesso, fechar o chamado com nota explicativa.",
            "Ligar para o usuario antes de ir. "
            "Registrar a tentativa (data, hora, resultado). "
            "Encerrar o chamado apos a 2a tentativa sem sucesso.",
        ),
        (
            "Para visitas tecnicas: o estagiario deve portar cracha "
            "institucional e ordem de servico. "
            "1) Apresentar-se ao usuario. "
            "2) Diagnosticar o problema. "
            "3) Executar o reparo ou documentar a necessidade de retirada.",
            "Levar cracha e ordem de servico. "
            "Seguir o checklist de atendimento presencial. "
            "Registrar o diagnostico e a acao tomada no ticket.",
        ),
        (
            "Quando o usuario solicita atendimento presencial mas o problema "
            "e de software: orientar a tentar atendimento remoto primeiro. "
            "Visita in loco so se o remoto nao resolver. "
            "Economiza tempo e prioriza casos que exigem presenca fisica.",
            "Oferecer suporte remoto via AnyDesk ou similar. "
            "Se nao resolver, agendar visita. "
            "Documentar a tentativa de atendimento remoto no ticket.",
        ),
        (
            "Atendimento em laboratorio ou sala compartilhada: avisar o "
            "responsavel do espaco com antecedencia. "
            "Verificar se ha restricoes de horario. "
            "Levar todo o material necessario para nao precisar voltar.",
            "Confirmar horario de funcionamento do espaco. "
            "Solicitar autorizacao do responsavel. "
            "Levar kit de ferramentas e pecas comuns.",
        ),
        (
            "Quando o usuario nao e encontrado na sala na primeira visita: "
            "ligar imediatamente e remarcar. "
            "Nao deixar equipamento da instituicao na sala sem supervisao. "
            "Registrar a ocorrencia para evitar contagem dupla de tentativas.",
            "Tentar contato telefonico. "
            "Remarcar dentro do prazo do chamado. "
            "Documentar a tentativa frustrada no ticket.",
        ),
    ],
    "Suprimento de Impressora": [
        (
            "O Almoxarifado so entrega toner novo mediante devolucao do "
            "usado. "
            "1) Confirmar modelo da impressora. "
            "2) Solicitar ao usuario que entregue o toner usado. "
            "3) Retirar o toner novo no Almoxarifado. "
            "4) Instalar e testar a impressora.",
            "Pedir o toner usado ao usuario. "
            "Levar ao Almoxarifado para troca. "
            "Instalar o novo e testar impressao de teste.",
        ),
        (
            "Para impressora travada, com papel preso ou erro mecanico: "
            "1) Desligar e ligar a impressora. "
            "2) Abrir tampas e remover papel preso cuidadosamente. "
            "3) Verificar bandejas. "
            "4) Se persistir, abrir chamado de manutencao.",
            "Reiniciar a impressora. "
            "Limpar a area do papel preso. "
            "Abrir chamado tecnico se o problema persistir.",
        ),
        (
            "Quando o usuario pedir cartucho de cor especifico (ciano, "
            "magenta, amarelo): aplicar a mesma regra do toner - troca "
            "mediante devolucao do cartucho usado. "
            "Verificar no sistema o estoque disponivel por modelo.",
            "Solicitar devolucao do cartucho vazio. "
            "Consultar estoque do modelo. "
            "Agendar a troca com o usuario.",
        ),
        (
            "Impressora com qualidade de impressao ruim (listras, falhas, "
            "cores desbotadas): provavelmente toner/cartucho no fim. "
            "1) Verificar nivel pelo painel da impressora. "
            "2) Agendar troca preventiva. "
            "3) Limpar cabecote se for jato de tinta.",
            "Avaliar nivel do suprimento. "
            "Agendar troca se abaixo de 20%. "
            "Para jato de tinta, rodar ciclo de limpeza.",
        ),
        (
            "Para suprimentos nao disponiveis no Almoxarifado: abrir "
            "pedido de compra. "
            "Informar ao usuario o prazo estimado. "
            "Oferecer impressora substituta em outra sala se o servico for urgente.",
            "Verificar estoque no sistema. "
            "Se zerado, abrir pedido de compra. "
            "Comunicar o prazo ao usuario.",
        ),
    ],
}


def main():
    df = pd.read_csv(ARQ, sep=";", encoding="utf-8")
    print(f"Dataset original: {len(df)} linhas")

    # Normaliza os nomes das categorias no dataset para o match nao quebrar
    # com diferenca de encoding (CSV tem 'Inservível' duplo-codificado).
    def _norm_cat(s):
        import unicodedata
        s = str(s)
        s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
        return s.strip().lower()

    df["_cat_norm"] = df["Categoria_Problema"].apply(_norm_cat)

    for categoria, variacoes in POPs.items():
        cat_norm = _norm_cat(categoria)
        mask = df["_cat_norm"] == cat_norm
        n = mask.sum()
        if n == 0:
            print(f"  [AVISO] Categoria nao encontrada no dataset: {categoria!r}")
            continue
        idxs = df.index[mask].tolist()
        for i, idx in enumerate(idxs):
            regra, acao = variacoes[i % len(variacoes)]
            df.at[idx, "Regra_POP"] = regra
            df.at[idx, "Acao_Correta_Estagiario"] = acao
        print(f"  [OK] {categoria}: {n} linhas atualizadas com {len(variacoes)} variacoes")

    df = df.drop(columns=["_cat_norm"])
    df.to_csv(ARQ, sep=";", encoding="utf-8", index=False)
    print(f"Dataset atualizado: {len(df)} linhas")
    print()
    print("Regras unicas por categoria (apos edicao):")
    for cat in df["Categoria_Problema"].unique():
        n = df[df["Categoria_Problema"] == cat]["Regra_POP"].nunique()
        total = (df["Categoria_Problema"] == cat).sum()
        print(f"  {cat}: {n} regras unicas (em {total} linhas)")


if __name__ == "__main__":
    main()
