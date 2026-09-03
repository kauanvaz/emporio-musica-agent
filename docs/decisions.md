# Fontes de dados

Há dois tipos diferentes:
 - Dados estruturados (produtos, pedidos, promoções, clientes. CSV)
 - Dados não estruturados (políticas em PDF). 
 
Isso determinou a arquitetura: ferramentas especializadas por tipo. Para dados estruturados, um agente Text-to-SQL sobre SQLite. Para o manual, um pipeline de Retrieval-Augmented Generation (RAG).

# Defesa em código de SQL

Um agente Text-to-SQL depende da saída da LLM, mas não se deve confiar nela cegamente. A execução de SQL deve ser protegida: comandos de escrita/destruição (INSERT, UPDATE, DELETE, DROP, etc.) são bloqueados e múltiplos statements são rejeitados. O banco é somente-leitura e em memória. Mesmo que o modelo ignore o prompt de sistema, há essa outra camada de proteção.