
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import urllib

# Configuração da página
st.set_page_config(
    page_title="Sistema de Recomendação Contoso",
    page_icon="🛍️",
    layout="wide"
)

# Título e descrição
st.title("🛍️ Sistema de Recomendação Contoso")
st.markdown("""
Sistema de recomendação baseado em Filtragem Colaborativa (User-Based Collaborative Filtering)
""")

# Função para conexão com o banco de dados
@st.cache_resource
def criar_conexao_banco():
    """Cria e retorna a conexão com o banco de dados"""
    servidor = "ARAUJO"
    banco = "ContosoRetailDW"
    
    # String de conexão para SQLAlchemy
    params = urllib.parse.quote_plus(
        f"Driver={{SQL Server}};"
        f"Server={servidor};"
        f"Database={banco};"
        f"Trusted_Connection=yes;"
    )
    
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}",pool_pre_ping=True)
    return engine

# Função para carregar dados
@st.cache_data
def carregar_dados():
    """Carrega os dados necessários do banco"""
    engine = criar_conexao_banco()
    
    # Carregar vendas
    query_vendas = """
        SELECT
        v.CustomerKey,
        v.ProductKey,
        SUM(v.SalesQuantity) as TotalQtd
        FROM vw_FactOnlineSales v
        INNER JOIN DimCustomer c ON v.CustomerKey = c.CustomerKey
        WHERE c.CustomerType = 'Person' -- Filtra apenas pessoas físicas
        GROUP BY v.CustomerKey, v.ProductKey
        """
    
    df_vendas = pd.read_sql(query_vendas, engine)
    
    # Carregar produtos
    query_produtos = "SELECT ProductKey, ProductName FROM vw_DimProduct"
    df_produtos = pd.read_sql(query_produtos, engine)
    
    # Carregar clientes
    query_clientes = """
    SELECT 
        CustomerKey, 
        CONCAT(FirstName, ' ', LastName) as nome_completo,
        EmailAddress,
        Gender
    FROM vw_DimCustomer 
    WHERE CustomerType = 'Person'
    """
    df_clientes = pd.read_sql(query_clientes, engine)
    
    return df_vendas, df_produtos, df_clientes

# Função para criar matriz de interação
def criar_matriz_interacao(df_vendas):
    """Cria a matriz cliente x produto"""
    matriz = df_vendas.pivot_table(
        index='CustomerKey',
        columns='ProductKey',
        values='TotalQtd',
        fill_value=0
    )
    return matriz

# Função para calcular similaridades
def calcular_similaridades(matriz):
    """Calcula a matriz de similaridade entre clientes"""
    similaridade = cosine_similarity(matriz)
    df_similaridade = pd.DataFrame(
        similaridade,
        index=matriz.index,
        columns=matriz.index
    )
    return df_similaridade

# Função para obter recomendações
def obter_recomendacoes(cliente_id, matriz, df_similaridade, n_vizinhos=5):
   
    """Obtém recomendações para um cliente específico"""
    # Produtos que o cliente já comprou
    produtos_comprados = set(matriz.loc[cliente_id][matriz.loc[cliente_id] > 0].index)
    
    # Encontrar clientes similares (excluindo o próprio)
    similares = df_similaridade[cliente_id].sort_values(ascending=False)[1:n_vizinhos+1]
    
    # Coletar produtos dos vizinhos que o cliente não comprou
    recomendacoes = {}
    
    for vizinho_id, similaridade_score in similares.items():
        produtos_vizinho = set(matriz.loc[vizinho_id][matriz.loc[vizinho_id] > 0].index)
        produtos_novos = produtos_vizinho - produtos_comprados
        
        for produto in produtos_novos:
            if produto not in recomendacoes:
                recomendacoes[produto] = {
                    'score': similaridade_score,
                    'vizinhos': [vizinho_id]
                }
            else:
                # Atualizar score (média ponderada)
                recomendacoes[produto]['vizinhos'].append(vizinho_id)
                recomendacoes[produto]['score'] = max(recomendacoes[produto]['score'], similaridade_score)
    
    # Ordenar recomendações por score
    recomendacoes_ordenadas = sorted(
        recomendacoes.items(),
        key=lambda x: x[1]['score'],
        reverse=True
    )
    
    return produtos_comprados, similares, recomendacoes_ordenadas

# Interface principal
def main():
    # Carregar dados
    with st.spinner("Carregando dados do banco..."):
        try:
            df_vendas, df_produtos, df_clientes = carregar_dados()
            
            # Criar matriz de interação
            matriz = criar_matriz_interacao(df_vendas)
            
            # Calcular similaridades
            df_similaridade = calcular_similaridades(matriz)
            
            st.success("✅ Dados carregados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            st.stop()
    
    # Sidebar para seleção do cliente
    st.sidebar.header("🔍 Configurações")
    
    # Seleção do cliente
    clientes_disponiveis = df_clientes['nome_completo'].tolist()
    cliente_selecionado = st.sidebar.selectbox(
        "Selecione um cliente:",
        clientes_disponiveis,
        index=0
    )
    
    # Obter ID do cliente selecionado
    cliente_id = df_clientes.loc[
        df_clientes['nome_completo'] == cliente_selecionado, 
        'CustomerKey'
    ].values[0]
    
    # Número de vizinhos para considerar
    n_vizinhos = st.sidebar.slider(
        "Número de vizinhos similares:",
        min_value=3,
        max_value=20,
        value=5
    )
    
    # Número de recomendações
    n_recomendacoes = st.sidebar.slider(
        "Número de recomendações:",
        min_value=1,
        max_value=10,
        value=3
    )
    
    # Informações do cliente
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Informações do Cliente")
    
    cliente_info = df_clientes[df_clientes['CustomerKey'] == cliente_id].iloc[0]
    st.sidebar.write(f"**ID:** {cliente_info['CustomerKey']}")
    st.sidebar.write(f"**Nome:** {cliente_info['nome_completo']}")
    st.sidebar.write(f"**Email:** {cliente_info['EmailAddress']}")
    st.sidebar.write(f"**Gênero:** {cliente_info['Gender']}")
    
    
    # Processar recomendações
    produtos_comprados, clientes_similares, recomendacoes = obter_recomendacoes(
        cliente_id, matriz, df_similaridade, n_vizinhos
    )
    
    # Layout principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header(f"📊 Análise para: {cliente_selecionado}")
        
        # Tab para diferentes visualizações
        tab1, tab2, tab3 = st.tabs([
            "📦 Produtos Comprados", 
            "🎯 Recomendações", 
            "👥 Clientes Similares"
        ])
        
        with tab1:
            if produtos_comprados:
                # Converter IDs de produtos para nomes
                produtos_comprados_nomes = df_produtos[
                    df_produtos['ProductKey'].isin(produtos_comprados)
                ]['ProductName'].tolist()
                
                st.write(f"**Total de produtos comprados:** {len(produtos_comprados)}")
                
                # Mostrar lista de produtos
                for i, produto in enumerate(produtos_comprados_nomes[:20], 1):
                    st.write(f"{i}. {produto}")
                
                if len(produtos_comprados_nomes) > 20:
                    st.write(f"... e mais {len(produtos_comprados_nomes) - 20} produtos")
            else:
                st.info("Este cliente ainda não realizou compras.")
        
        with tab2:
            if recomendacoes:
                st.write(f"**Recomendações baseadas em {n_vizinhos} clientes similares:**")
                
                for i, (produto_id, info) in enumerate(recomendacoes[:n_recomendacoes], 1):
                    produto_nome = df_produtos[
                        df_produtos['ProductKey'] == produto_id
                    ]['ProductName'].values[0]
                    
                    # Calcular percentual de confiança
                    confianca_percentual = info['score'] * 100
                    
                    # Criar métrica visual
                    st.markdown(f"### {i}. {produto_nome}")
                    st.progress(float(info['score']))
                    st.write(f"**Confiança:** {confianca_percentual:.2f}%")
                    st.write(f"**Baseado em:** {len(info['vizinhos'])} cliente(s) similar(es)")
                    st.write("---")
            else:
                st.info("Não há recomendações disponíveis para este cliente.")
        
        with tab3:
            if not clientes_similares.empty:
                st.write(f"**Top {len(clientes_similares)} clientes mais similares:**")
                
                # Criar DataFrame para visualização
                similares_df = pd.DataFrame({
                    'ID do Cliente': clientes_similares.index,
                    'Similaridade': (clientes_similares.values * 100).round(2)
                })
                
                # Adicionar nomes dos clientes
                similares_df = similares_df.merge(
                    df_clientes[['CustomerKey', 'nome_completo']],
                    left_on='ID do Cliente',
                    right_on='CustomerKey'
                )
                
                # Mostrar tabela
                st.dataframe(
                    similares_df[['nome_completo', 'ID do Cliente', 'Similaridade']],
                    hide_index=True,
                    column_config={
                        "nome_completo": "Nome do Cliente",
                        "ID do Cliente": "ID",
                        "Similaridade": st.column_config.NumberColumn(
                            "Similaridade (%)",
                            format="%.2f %%"
                        )
                    }
                )
                
                # Gráfico de similaridade
                fig = px.bar(
                    similares_df,
                    x='nome_completo',
                    y='Similaridade',
                    title='Similaridade com Outros Clientes',
                    labels={'Similaridade': 'Similaridade (%)', 'nome_completo': 'Cliente'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não foram encontrados clientes similares.")
    
    with col2:
        st.header("📈 Métricas")
        
        # Métricas principais
        metric_col1, metric_col2 = st.columns(2)
        
        with metric_col1:
            st.metric(
                label="Produtos Comprados",
                value=len(produtos_comprados)
            )
            
            if recomendacoes:
                st.metric(
                    label="Recomendações Disponíveis",
                    value=len(recomendacoes)
                )
        
        with metric_col2:
            st.metric(
                label="Clientes Similares",
                value=len(clientes_similares)
            )
            
            if clientes_similares.empty:
                similaridade_max = 0
            else:
                similaridade_max = clientes_similares.max() * 100
                st.metric(
                    label="Similaridade Máxima",
                    value=f"{similaridade_max:.1f}%"
                )
        
        st.markdown("---")
        
        # Visualização da matriz de similaridade (simplificada)
        st.subheader("🔗 Rede de Similaridade")
        
        if not clientes_similares.empty:
            # Criar gráfico de rede simplificado
            fig = go.Figure()
            
            # Adicionar nós
            fig.add_trace(go.Scatter(
                x=[0], y=[0],
                mode='markers+text',
                marker=dict(size=30, color='red'),
                text=[cliente_selecionado.split()[0]],
                textposition="top center",
                name="Cliente Selecionado"
            ))
            
            # Adicionar clientes similares
            for i, (vizinho_id, score) in enumerate(clientes_similares.items(), 1):
                angle = (i * 2 * np.pi) / len(clientes_similares)
                x = np.cos(angle)
                y = np.sin(angle)
                
                vizinho_nome = df_clientes[
                    df_clientes['CustomerKey'] == vizinho_id
                ]['nome_completo'].values[0].split()[0]
                
                fig.add_trace(go.Scatter(
                    x=[x], y=[y],
                    mode='markers+text',
                    marker=dict(size=20, color='blue'),
                    text=[vizinho_nome],
                    textposition="top center",
                    name=f"Similaridade: {score*100:.1f}%"
                ))
                
                # Adicionar linha de conexão
                fig.add_trace(go.Scatter(
                    x=[0, x], y=[0, y],
                    mode='lines',
                    line=dict(width=score*3, color='gray'),
                    showlegend=False
                ))
            
            fig.update_layout(
                title="Relação com Clientes Similares",
                showlegend=True,
                height=400,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Detalhes técnicos
        with st.expander("🔧 Detalhes Técnicos"):
            st.write(f"**Total de clientes na base:** {len(matriz)}")
            st.write(f"**Total de produtos na base:** {len(matriz.columns)}")
            st.write(f"**Densidade da matriz:** {(matriz > 0).sum().sum() / (matriz.shape[0] * matriz.shape[1]) * 100:.2f}%")
    
    # Rodapé
    st.markdown("---")
    st.caption("Sistema de Recomendação Contoso - Baseado em Filtragem Colaborativa User-Based")

if __name__ == "__main__":
    main()