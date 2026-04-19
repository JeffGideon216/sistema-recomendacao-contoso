# 🎯 81.65% de confiança — produto certo, cliente certo, no momento certo

**Sistema de Recomendação B2C | Contoso Retail**

> Em um catálogo com 466 produtos e 2.154 clientes, qual item apresentar para cada pessoa para maximizar a chance de venda cruzada? Este sistema responde com precisão matemática.

---

## O problema real

Equipes de marketing e vendas frequentemente trabalham com campanhas genéricas — o mesmo e-mail, o mesmo produto, para toda a base. O resultado é desperdício de verba e baixa conversão. A pergunta que muda esse jogo:

> *"O que esse cliente específico tem maior probabilidade de comprar, baseado em clientes com comportamento idêntico ao dele?"*

---

## O que este sistema faz

Implementa um **motor de recomendação por Filtragem Colaborativa (User-Based)** que identifica clientes com padrão de consumo semelhante e usa esse comportamento coletivo para recomendar itens ainda não adquiridos pelo cliente-alvo.

**Saída concreta:**

```
🎯 CLIENTE ALVO: Briana Ortega (ID: 18347)
--------------------------------------------------
👥 CLIENTES SEMELHANTES (VIZINHOS):
- Cliente ID 114  → Afinidade: 81.65%
- Cliente ID 1744 → Afinidade: 79.32%
- Cliente ID 1745 → Afinidade: 76.18%

📦 ITEM SUGERIDO PARA CAMPANHA:
✅ [Produto recomendado com base no comportamento dos vizinhos]
```

---

## Como funciona

### 1. Curadoria de dados — o diferencial crítico (SQL Server)
```sql
SELECT v.CustomerKey, v.ProductKey, SUM(v.SalesQuantity) as TotalQtd 
FROM vw_FactOnlineSales v
INNER JOIN DimCustomer c ON v.CustomerKey = c.CustomerKey
WHERE c.CustomerType = 'Person'  -- Remove ruído B2B
GROUP BY v.CustomerKey, v.ProductKey
```
A base original misturava clientes corporativos (B2B) com pessoas físicas (B2C), distorcendo os padrões de consumo. A filtragem por `CustomerType = 'Person'` foi o passo que tornou o modelo confiável.

### 2. Construção da Matriz de Interação (Álgebra Linear)
```python
# Matriz esparsa: 2.154 usuários × 466 produtos
matriz_colaborativa = df_vendas.pivot(
    index='CustomerKey', 
    columns='ProductKey', 
    values='TotalQtd'
).fillna(0)
```

### 3. Similaridade de Cosseno — por que não distância euclidiana?
```python
user_sim = cosine_similarity(matriz_colaborativa)
```

A escolha pelo **cosseno** (não pela distância euclidiana) é intencional: o modelo foca na *orientação do gosto* do cliente, não na *quantidade* que ele compra. Um cliente que comprou 1 unidade de produto A e 1 de B tem o mesmo perfil de preferência que alguém que comprou 10 de A e 10 de B — e o cosseno captura isso.

### 4. Geração da recomendação
```python
# Encontra o vizinho mais próximo (excluindo o próprio cliente)
vizinho_top = similaridades.index[1]

# Recomenda o que o vizinho comprou e o cliente-alvo ainda não tem
recomendacoes = compras_vizinho[(compras_vizinho > 0) & (compras_alvo == 0)]
```

---

## Arquitetura do projeto

```
SQL Server (ContosoRetailDW)
    └── vw_FactOnlineSales + DimCustomer
            └── Filtro B2C (CustomerType = 'Person')
                    └── Matriz Esparsa [2154 × 466]
                            └── Similaridade de Cosseno
                                    └── Top-N Vizinhos
                                            └── Recomendação personalizada
```

---

## Stack técnico

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![SQL Server](https://img.shields.io/badge/SQL_Server-ContosoRetailDW-red?logo=microsoftsqlserver)
![Pandas](https://img.shields.io/badge/Pandas-Data_Engineering-150458?logo=pandas)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-Cosine_Similarity-F7931E?logo=scikit-learn)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-D71F00)

---

## Métricas do modelo

| Dimensão | Valor |
|----------|-------|
| Usuários na matriz | 2.154 |
| Produtos no catálogo | 466 |
| Densidade da matriz | Esparsa (tratada com `.fillna(0)`) |
| Confiança da recomendação (caso Briana Ortega) | **81.65%** |
| Método de similaridade | Cosseno (User-Based CF) |

---

## Por que Filtragem Colaborativa e não baseada em conteúdo?

A abordagem baseada em conteúdo (Content-Based) recomenda produtos similares ao que o cliente já comprou — ignora o comportamento coletivo. A Filtragem Colaborativa explora o padrão de **grupos de clientes semelhantes**, descobrindo produtos que o cliente provavelmente não conhece, mas que seu "gêmeo de comportamento" já validou. Para varejo com catálogo amplo, isso gera recomendações mais surpreendentes e com maior potencial de venda cruzada.

---

## Próximos passos

- [ ] Expandir para Top-N recomendações (não apenas 1 produto)
- [ ] Implementar validação com métricas de avaliação (Precision@K, Recall@K)
- [ ] Interface Streamlit para simulação interativa por ID de cliente

---

## Autor

**Jefferson da Silva Araújo**  
Analista de Dados | Logística & Supply Chain | Python · SQL · Machine Learning

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Jefferson_Araujo-0A66C2?logo=linkedin)](www.linkedin.com/in/
jefferson-analise-dados
)
[![GitHub](https://img.shields.io/badge/GitHub-JeffGideon216-181717?logo=github)](https://github.com/JeffGideon216)
[![Portfólio BI](https://img.shields.io/badge/Portfólio-Power_BI-F2C811?logo=powerbi)](https://bit.ly/4cDSp4x)

