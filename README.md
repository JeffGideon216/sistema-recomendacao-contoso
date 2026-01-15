# 📊 Relatório Técnico: Sistema de Recomendação B2C (Contoso)
# 1. Visão Geral do Projeto
Este projeto implementa um motor de recomendação baseado em Filtragem Colaborativa (User-Based Collaborative Filtering), utilizando dados transacionais do banco SQL Server (Contoso Retail) e processamento em Python.

# 2. Arquitetura de Dados e Tecnologias
Banco de Dados: SQL Server (Views Otimizadas).

Linguagem: Python 3.x.

Bibliotecas: Pandas (Manipulação), Scikit-Learn (Matemática de Similaridade).

# 3. Engenharia de Dados & Refinamento B2C
Um diferencial crítico deste projeto foi a Curadoria de Dados. Inicialmente, a base continha ruídos de clientes corporativos (B2B) que distorciam os padrões de consumo.

# 4. Técnicas de Machine Learning Aplicadas
**A**. Construção da Matriz de Interação (Matriz Esparsa)
Transformamos as vendas em uma matriz onde as linhas representam os clientes e as colunas os produtos.

Dimensões: 2154 usuários x 466 produtos.

Densidade: Tratamento de valores nulos com .fillna(0), preparando os vetores para cálculo de distância.

**B**. Similaridade de Cosseno (Álgebra Linear)
Utilizamos a técnica de cosseno para medir o ângulo entre os vetores de consumo de cada usuário.

O "Porquê": Diferente da distância euclidiana, o cosseno foca na orientação do gosto do cliente, não apenas na quantidade.

