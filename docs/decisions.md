# Fontes de dados

Há dois tipos diferentes:
 - Dados estruturados (produtos, pedidos, promoções, clientes. CSV)
 - Dados não estruturados (políticas em PDF). 
 
Isso determinou a arquitetura: ferramentas especializadas por tipo. Para dados estruturados, um agente Text-to-SQL sobre SQLite. Para o manual, um pipeline de Retrieval-Augmented Generation (RAG).
