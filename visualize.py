import pandas as pd
import plotly.graph_objects as go
import sqlite3
import streamlit as st

# Carregar os dados do banco de dados
def carregar_boxes():
    # Conectar ao banco de dados
    conn = sqlite3.connect("boxchain.db")
    cursor = conn.cursor()

    # Criar a tabela se não existir
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS boxes (
        id INTEGER PRIMARY KEY,
        tipo TEXT,
        modelo TEXT,
        nome_dispositivo TEXT,
        complemento TEXT,
        comodatario TEXT,
        data_transacao TEXT,
        data_comodato TEXT,
        chave_anterior TEXT,
        hash TEXT
    )
    """)
    conn.commit()

    # Tentar buscar os dados da tabela
    try:
        query = "SELECT id, tipo, modelo, nome_dispositivo, comodatario, chave_anterior, hash FROM boxes"
        df = pd.read_sql_query(query, conn)
    except pd.errors.DatabaseError as e:
        print(f"Erro ao tentar carregar os dados: {e}")
        df = pd.DataFrame()  # Retorna um DataFrame vazio se falhar
    finally:
        conn.close()

    return df

# Chamada para testar
df = carregar_boxes()
print(df)

# Converter a chave anterior em conexões
def criar_grafo(df):
    nodes = []
    edges = []
    
    for index, row in df.iterrows():
        # Adicionar cada box como um nó
        nodes.append({
            "id": row["id"],
            "label": f"Box {row['id']}",
            "x": index * 10,  # Posição X para visualização
            "y": 0,           # Posição Y para visualização
            "z": 0            # Posição Z para visualização
        })
        # Adicionar arestas para a chave anterior
        if row["chave_anterior"] != "0":
            anterior_id = df[df["hash"] == row["chave_anterior"]]["id"].values
            if len(anterior_id) > 0:
                edges.append({
                    "source": row["id"],
                    "target": anterior_id[0]
                })

    return nodes, edges

# Criar visualização 3D
def visualizar_3d(nodes, edges):
    fig = go.Figure()

    # Adicionar nós
    for node in nodes:
        fig.add_trace(go.Scatter3d(
            x=[node["x"]],
            y=[node["y"]],
            z=[node["z"]],
            mode="markers+text",
            text=[node["label"]],
            marker=dict(size=10, color="blue"),
        ))

    # Adicionar conexões
    for edge in edges:
        source = next(node for node in nodes if node["id"] == edge["source"])
        target = next(node for node in nodes if node["id"] == edge["target"])
        fig.add_trace(go.Scatter3d(
            x=[source["x"], target["x"]],
            y=[source["y"], target["y"]],
            z=[source["z"], target["z"]],
            mode="lines",
            line=dict(width=2, color="gray")
        ))

    fig.update_layout(
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z"
        ),
        title="Visualização 3D das Boxes",
    )
    return fig

# Streamlit UI
st.title("Visualização 3D da BoxChain")

df = carregar_boxes()
nodes, edges = criar_grafo(df)
fig = visualizar_3d(nodes, edges)

st.plotly_chart(fig)
