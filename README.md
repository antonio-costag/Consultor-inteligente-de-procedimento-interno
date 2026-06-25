# Consultor Inteligente de Procedimentos Internos

Trabalho avaliativo para a materia de Inteligencia Artificial

## Melhorias Implementadas na Versão Final

Este projeto implementou uma **busca semântica** usando TF-IDF (Term Frequency-Inverse Document Similarity) para substituir a antiga busca por correspondência exata de palavras (`str.contains()`), tornando o sistema verdadeiramente inteligente na compreensão de consultas dos usuários.

### Problema Original
A busca anterior usava `str.contains()` que só encontrava correspondências exatas de palavras:
- Usuário pesquisa: "Impressora" 
- Sistema só encontrava se houvesse exatamente "Impressora" nos dados
- Falhava com sinônimos como "Equipamento de impressão", "dispositivo de saída", etc.

### Solução Implementada
Substituímos a busca por palavra-chave por **busca semântica** que:

1. **Vetoriza o texto**: Converte procedimentos em vetores numéricos usando TF-IDF
2. **Mede similaridade semântica**: Usa cosine similarity para encontrar conceitos relacionados
3. **Recupera contexto relevante**: Encontra procedimentos similares mesmo sem palavras exatas

### Exemplo de Melhoria
**Consulta do usuário**: "Minha impressão não está funcionando"
**Antes**: Nenhum resultado (sem correspondência exata de palavras)
**Depois**: Encontra procedimentos sobre "Equipamento de impressão" e "dispositivo de saída" por similaridade semântica

### Como Funciona
1. **Pré-processamento**: Combina Categoria_Problema + Regra_POP + Descricao_Chamado em documentos ricos
2. **Vetorização**: TF-IDF cria matriz de características (unigramas e bigramas, remove stop words em português)
3. **Consulta**: Vetoriza a pergunta do usuário no mesmo espaço
4. **Similaridade**: Calcula cosine similarity entre consulta e todos os documentos
5. **Recuperação**: Seleciona top-3 procedimentos mais similares semanticamente
6. **Geração**: Envia resultados para o Gemini gerar resposta final

### Tecnologias Adicionadas
- **scikit-learn**: Para TF-IDF Vectorizer e cosine similarity
- **numpy**: Suporte numérico para operações vetoriais

### Benefícios
- ✅ Compreende sinônimos e conceitos relacionados
- ✅ Funciona com erros de digitação leves (graças ao TF-IDF)
- ✅ Recupera procedimentos relevantes mesmo com formulagem diferente
- ✅ Mantém compatibilidade com busca exata quando apropriado
- ✅ Baseado em técnicas ensinadas na aula 07 (Clustering e PCA - conceitos de vetorização)

## Como Executar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute o programa:
   ```bash
   python main.py
   ```

## Estrutura do Projeto
- `main.py`: Aplicação principal com busca semântica implementada
- `dataset_suporte_interno_sintetico.csv.xls`: Base de procedimentos (CSV com separador ;)
- `requirements.txt`: Dependências incluindo scikit-learn para busca semântica
- `README.md`: Este arquivo

## Observações
- Requer conexão com internet para API do Gemini
- Índice semântico construído na inicialização para performance
- Mantém todas as funcionalidades originais (trilhas de treinamento, simulador)