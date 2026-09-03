# Fontes de dados

Há dois tipos diferentes:
 - Dados estruturados (produtos, pedidos, promoções, clientes. CSV)
 - Dados não estruturados (políticas em PDF). 
 
Isso determinou a arquitetura: ferramentas especializadas por tipo. Para dados estruturados, um agente Text-to-SQL sobre SQLite. Para o manual, um pipeline de Retrieval-Augmented Generation (RAG).

# Defesa em código de SQL

Um agente Text-to-SQL depende da saída da LLM, mas não se deve confiar nela cegamente. A execução de SQL deve ser protegida: comandos de escrita/destruição (INSERT, UPDATE, DELETE, DROP, etc.) são bloqueados e múltiplos statements são rejeitados. O banco é somente-leitura e em memória. Mesmo que o modelo ignore o prompt de sistema, há essa outra camada de proteção.

# RAG

Para os dados não estruturados (manual de políticas), o ideal é um pipeline de Retrieval-Augmented Generation: extração do PDF, divisão em trechos (chunks) e indexação vetorial (FAISS). Quando o cliente pergunta sobre regras (troca, pagamento, horários) o agente consulta esta ferramenta e usa os trechos recuperados como contexto, em vez de memorizar ou inventar a política.


# Problemas encontrados após primeira rodada de testes

Você: Como posso entrar em contato com a loja?

Assistente: Desculpe, mas não tenho essa informação. Recomendo que você verifique o site da loja ou suas redes sociais para encontrar os dados de contato. Se precisar de ajuda com produtos ou políticas da loja, estou à disposição!


Problema: deveria retornar informações de contato

-----------------------------------------------------------------------------------------------------------------------------------------------------------
Você: Tem ukulele?

Assistente: Atualmente, não temos ukuleles disponíveis em nosso estoque. Se precisar de ajuda com outro produto ou tiver mais perguntas, estou à disposição!


Problema: existem ukuleles no estoque

-----------------------------------------------------------------------------------------------------------------------------------------------------------

Você: Quais são as promoções disponíveis?

Assistente: Atualmente, temos as seguintes promoções ativas na loja:

1. **Oferta Especial**: 10% de desconto
2. **Desconto Exclusivo**: 20% de desconto
3. **Desconto Exclusivo**: 8% de desconto
4. **Desconto Exclusivo**: 18% de desconto


Problema: promoções para quais produtos? Não especificou
