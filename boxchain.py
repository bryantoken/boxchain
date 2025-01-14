import hashlib
import datetime
import sqlite3
import streamlit as st
from visualize import carregar_boxes, criar_grafo, visualizar_3d

# Classe para o complemento
def create_complemento(mouse, teclado, monitor1, monitor2, fonte):
    return {
        "Mouse": mouse,
        "Teclado": teclado,
        "Monitor1": monitor1,
        "Monitor2": monitor2,
        "Fonte": fonte
    }

# Classe para representar um bloco
class Box:
    def __init__(self, id, tipo, modelo, nome_dispositivo, complemento, comodatario, data_transacao, data_comodato=None, chave_anterior="0"):
        self.chave_anterior = chave_anterior
        self.id = id
        self.tipo = tipo
        self.modelo = modelo
        self.nome_dispositivo = nome_dispositivo
        self.complemento = complemento
        self.comodatario = comodatario
        self.data_transacao = data_transacao
        self.data_comodato = data_comodato
        self.hash = self.gerar_hash()

    def gerar_hash(self):
        # Cria uma hash única para o bloco com base nos seus dados
        dados = (
            str(self.chave_anterior) +
            str(self.id) +
            self.tipo +
            self.modelo +
            self.nome_dispositivo +
            str(self.complemento) +
            self.comodatario +
            self.data_transacao +
            (self.data_comodato or "")
        )
        return hashlib.sha256(dados.encode()).hexdigest()

# Inicializar banco de dados
conn = sqlite3.connect("boxchain.db")
cursor = conn.cursor()

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

# Função para salvar box no banco de dados
def salvar_box(box):
    cursor.execute(
        """
        INSERT INTO boxes (id, tipo, modelo, nome_dispositivo, complemento, comodatario, data_transacao, data_comodato, chave_anterior, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            box.id,
            box.tipo,
            box.modelo,
            box.nome_dispositivo,
            str(box.complemento),
            box.comodatario,
            box.data_transacao,
            box.data_comodato,
            box.chave_anterior,
            box.hash,
        )
    )
    conn.commit()

# Função para criar um novo bloco na blockchain
def criar_box(tipo, modelo, nome_dispositivo, complemento, comodatario, data_comodato):
    cursor.execute("SELECT * FROM boxes ORDER BY id DESC LIMIT 1")
    ultimo_bloco = cursor.fetchone()
    
    if ultimo_bloco:
        chave_anterior = ultimo_bloco[9]  # A chave anterior é a última chave do bloco anterior
        id = ultimo_bloco[0] + 1
    else:
        chave_anterior = "0"  # Se for o primeiro bloco, a chave anterior é 0
        id = 1
        tipo = "Genesis"  # Primeira box como Genesis

    data_transacao = datetime.datetime.now().strftime("%d/%m/%Y")
    novo_box = Box(
        id=id,
        tipo=tipo,
        modelo=modelo,
        nome_dispositivo=nome_dispositivo,
        complemento=complemento,
        comodatario=comodatario,
        data_transacao=data_transacao,
        data_comodato=data_comodato,
        chave_anterior=chave_anterior,
    )
    salvar_box(novo_box)
    return novo_box

# Streamlit UI
st.title("BoxChain - Gerenciamento de Boxes")

menu = st.sidebar.selectbox("Menu", ["Criar Box", "Alterar Comodatário", "Visualizar Blockchain"])

if menu == "Criar Box":
    st.header("Criar Nova Box")

    modelo = st.text_input("Modelo", "Dell Inspiron 15")
    nome_dispositivo = st.text_input("Nome do Dispositivo", "DESKTOP-EZK1859")
    mouse = st.text_input("Mouse", "Mouse")
    teclado = st.text_input("Teclado", "Teclado")
    monitor1 = st.text_input("Monitor 1", "Monitor 1")
    monitor2 = st.text_input("Monitor 2", "Monitor 2")
    fonte = st.text_input("Fonte", "Fonte")
    complemento = create_complemento(mouse, teclado, monitor1, monitor2, fonte)
    comodatario = st.text_input("Comodatário", "Luiz Felippe")
    data_comodato = st.date_input("Data do Comodato")

    if st.button("Criar Box"):
        novo_box = criar_box("Transação", modelo, nome_dispositivo, complemento, comodatario, data_comodato.strftime("%d/%m/%Y"))
        st.success(f"Box criado com sucesso! ID: {novo_box.id}")

elif menu == "Alterar Comodatário":
    st.header("Alterar Comodatário")

    box_id = st.number_input("ID da Box", min_value=1, step=1)
    novo_comodatario = st.text_input("Novo Comodatário")
    nova_data_comodato = st.date_input("Nova Data do Comodato")

    if st.button("Alterar Comodatário"):
        cursor.execute("SELECT * FROM boxes WHERE id = ?", (box_id,))
        box_atual = cursor.fetchone()

        if box_atual:
            novo_box = criar_box(
                tipo="Transação",
                modelo=box_atual[2],
                nome_dispositivo=box_atual[3],
                complemento=eval(box_atual[4]),
                comodatario=novo_comodatario,
                data_comodato=nova_data_comodato.strftime("%d/%m/%Y")
            )
            st.success("Comodatário atualizado e novo bloco criado com sucesso!")
        else:
            st.error("Box não encontrada!")

elif menu == "Visualizar Blockchain":
    st.header("Blockchain Completa")
    
    # Filtros
    filtro_nome = st.text_input("Filtrar por Nome do Dispositivo", "")
    filtro_comodatario = st.text_input("Filtrar por Comodatário", "")
    
    # Consulta SQL com filtros e ordenação
    query = "SELECT * FROM boxes WHERE nome_dispositivo LIKE ? AND comodatario LIKE ? ORDER BY id DESC"
    cursor.execute(query, ('%' + filtro_nome + '%', '%' + filtro_comodatario + '%'))
    boxes = cursor.fetchall()

    st.title("Visualização da BoxChain")
    df = carregar_boxes()
    nodes, edges = criar_grafo(df)

    # Gerar visualização
    fig = visualizar_3d(nodes, edges)
    st.plotly_chart(fig)

    for box in boxes:
        st.text(f"ID: {box[0]}\nTipo: {box[1]}\nModelo: {box[2]}\nNome do Dispositivo: {box[3]}\nComplemento: {box[4]}\nComodatário: {box[5]}\nData Transação: {box[6]}\nData Comodato: {box[7]}\nChave Anterior: {box[8]}\nHash: {box[9]}\n")
        st.text("-" * 50)
