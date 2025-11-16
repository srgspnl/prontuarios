import json
import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from bson.json_util import dumps
import io

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Extrator MongoDB",
    page_icon="📊",
    layout="wide"
)

# CSS customizado
st.markdown("""
<style>
    .stats-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .stats-number {
        font-size: 2.5em;
        font-weight: bold;
    }
    .stats-label {
        font-size: 1em;
        opacity: 0.9;
    }
    .json-container {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .json-header {
        background-color: #2d2d2d;
        color: #4CAF50;
        padding: 12px 20px;
        border-radius: 8px 8px 0 0;
        font-weight: bold;
        font-size: 1.1em;
        margin: 15px 0 0 0;
        border-left: 4px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# ==================== FUNÇÃO DE NORMALIZAÇÃO ====================

def normalizar_documento(doc):
    """
    Normaliza um documento JSON/BSON, achatando suas chaves (flattening) 
    e convertendo valores para string de forma segura.
    """
    doc_json = json.loads(dumps(doc))
    
    def achatar(d, chave_pai='', sep='.'):
        itens = []
        for k, v in d.items():
            nova_chave = f"{chave_pai}{sep}{k}" if chave_pai else k
            
            if isinstance(v, dict):
                itens.extend(achatar(v, nova_chave, sep=sep).items())
            elif isinstance(v, list):
                itens.append((nova_chave, json.dumps(v, ensure_ascii=False)))
            else:
                itens.append((nova_chave, str(v)))
                
        return dict(itens)
        
    return achatar(doc_json)

# ==================== FUNÇÃO DE FORMATAÇÃO JSON ====================

def formatar_json_mongodb(doc):
    """
    Formata o documento no estilo MongoDB Atlas (JSON com indentação)
    """
    # Converte BSON para JSON mantendo a estrutura original
    doc_json = json.loads(dumps(doc))
    return json.dumps(doc_json, indent=2, ensure_ascii=False)

# ==================== FUNÇÃO DE EXTRAÇÃO ====================

def buscar_e_gerar_dados(mongo_uri, database_name, collection_name):
    """
    Conecta ao MongoDB e busca os documentos.
    Retorna (sucesso, conteudo_txt, documentos_originais, num_documentos)
    """
    client = None
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[database_name]
        collection = db[collection_name]
        client.server_info()
        
        documentos = list(collection.find())
        
        # Gerar conteúdo TXT (formato achatado)
        output = io.StringIO()
        output.write(f"--- RELATÓRIO DE DOCUMENTOS MONGODB (Formato Achatado) ---\n")
        output.write(f"Data de Geração: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write("-" * 70 + "\n\n")
        
        for idx, doc in enumerate(documentos):
            dados_achatados = normalizar_documento(doc)
            
            output.write(f"== DOCUMENTO {idx + 1} ==")
            output.write(f" (ID: {dados_achatados.get('_id.$oid', 'N/A')})\n")
            
            for chave, valor in dados_achatados.items():
                output.write(f"{chave}: {valor}\n")
                
            output.write("-" * 70 + "\n\n")
        
        conteudo_txt = output.getvalue()
        output.close()
        
        return True, conteudo_txt, documentos, len(documentos)
        
    except Exception as e:
        return False, str(e), [], 0
        
    finally:
        if client:
            client.close()

# ==================== INTERFACE STREAMLIT ====================

st.title("📊 Extrator de Documentos MongoDB")
st.markdown("### Sistema de Visualização e Exportação de Dados")
st.markdown("---")

# Formulário de credenciais
with st.form("credenciais_form"):
    st.subheader("🔐 Credenciais do Banco de Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        usuario = st.text_input("Usuário", value="admin", help="Usuário do MongoDB")
        database = st.text_input("Database", value="context", help="Nome do banco de dados")
    
    with col2:
        senha = st.text_input("Senha", type="password", help="Digite 12 caracteres (apenas os 8 primeiros serão usados)")
        collection = st.text_input("Coleção", value="SaudeTeste", help="Nome da coleção")
    
    host = st.text_input(
        "Host/Cluster", 
        value="cluster0.rfdha.gcp.mongodb.net",
        help="Endereço do cluster MongoDB"
    )
    
    submitted = st.form_submit_button("🚀 Conectar e Extrair Dados", type="primary", use_container_width=True)

# Processamento após submit
if submitted:
    if not senha:
        st.error("⚠️ Por favor, informe a senha do banco de dados.")
    elif len(senha) < 12:
        st.error("⚠️ A senha deve ter exatamente 12 caracteres.")
    else:
        # Usar apenas os 8 primeiros caracteres da senha
        senha_utilizada = senha[:8]
        mongo_uri = f"mongodb+srv://{usuario}:{senha_utilizada}@{host}/{database}?retryWrites=true&w=majority"
        
        with st.spinner("🔄 Conectando ao MongoDB e extraindo dados..."):
            sucesso, resultado_txt, documentos_originais, num_docs = buscar_e_gerar_dados(mongo_uri, database, collection)
        
        if sucesso:
            st.success(f"✅ Conexão estabelecida com sucesso!")
            
            # Estatísticas
            col1, col2, col3 = st.columns(3)
            
            # Calcular quantidade com blockchain (verifica campo blockchain_info)
            documentos_com_blockchain = sum(1 for doc in documentos_originais 
                                           if 'blockchain_info' in doc and doc['blockchain_info'])
            
            with col1:
                st.markdown(f"""
                <div class="stats-box">
                    <div class="stats-number">{num_docs}</div>
                    <div class="stats-label">Documentos</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="stats-box" style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);">
                    <div class="stats-number">{documentos_com_blockchain}</div>
                    <div class="stats-label">🔗 Com Blockchain</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                documentos_sem_blockchain = num_docs - documentos_com_blockchain
                st.markdown(f"""
                <div class="stats-box" style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);">
                    <div class="stats-number">{documentos_sem_blockchain}</div>
                    <div class="stats-label">📄 Sem Blockchain</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Visualização em formato MongoDB Atlas
            st.markdown("### 📋 Documentos (Formato MongoDB Atlas)")
            
            # Controle de paginação
            docs_por_pagina = 10
            if num_docs > docs_por_pagina:
                pagina = st.number_input(
                    "Página", 
                    min_value=1, 
                    max_value=(num_docs // docs_por_pagina) + 1,
                    value=1,
                    help=f"Exibindo {docs_por_pagina} documentos por página"
                )
                inicio = (pagina - 1) * docs_por_pagina
                fim = min(inicio + docs_por_pagina, num_docs)
                docs_exibir = documentos_originais[inicio:fim]
                idx_offset = inicio
                
                st.info(f"📄 Exibindo documentos {inicio + 1} a {fim} de {num_docs}")
            else:
                docs_exibir = documentos_originais
                idx_offset = 0
            
            # Renderizar cada documento em formato JSON
            for idx, doc in enumerate(docs_exibir):
                doc_num = idx + idx_offset + 1
                doc_id = str(doc.get('_id', 'N/A'))
                
                # Verificar se existe marca de blockchain (campo blockchain_info)
                tem_blockchain = 'blockchain_info' in doc and doc['blockchain_info']
                
                # Cor e ícone baseado na presença de blockchain
                if tem_blockchain:
                    cor_borda = "#4CAF50"  # Verde
                    icone = "🔗⛓️"
                    status_text = "REGISTRADO EM BLOCKCHAIN"
                else:
                    cor_borda = "#FF9800"  # Laranja
                    icone = "📄"
                    status_text = "SEM REGISTRO BLOCKCHAIN"
                
                # Header do documento com indicação de blockchain
                st.markdown(f"""
                <div class="json-header" style="border-left: 4px solid {cor_borda};">
                    {icone} Documento {doc_num} - ID: {doc_id}
                    <span style="float: right; font-size: 0.85em; background-color: {'#4CAF50' if tem_blockchain else '#FF9800'}; 
                          padding: 4px 12px; border-radius: 12px; color: white;">
                        {status_text}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                # JSON formatado
                json_formatado = formatar_json_mongodb(doc)
                st.code(json_formatado, language='json')
            
            # Aba para formato achatado (TXT)
            st.markdown("---")
            with st.expander("📄 Ver Formato Achatado (TXT)", expanded=False):
                st.text_area("Conteúdo Achatado", resultado_txt, height=400)
            
            # Botão de download
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                # Download formato achatado
                st.download_button(
                    label="📥 Download Formato Achatado (.txt)",
                    data=resultado_txt,
                    file_name=f"relatorio_achatado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                # Download formato JSON original
                json_completo = json.dumps(
                    [json.loads(dumps(doc)) for doc in documentos_originais],
                    indent=2,
                    ensure_ascii=False
                )
                st.download_button(
                    label="📥 Download Formato JSON (.json)",
                    data=json_completo,
                    file_name=f"documentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        else:
            st.error("❌ **Falha de Conexão**")
            with st.expander("🔍 Detalhes do Erro"):
                st.code(resultado_txt)
            
            st.info("""
            💡 **Dicas de Troubleshooting:**
            - ✓ Verifique se a senha está correta
            - ✓ Confirme se o IP está liberado no MongoDB Atlas (Network Access)
            - ✓ Verifique se o cluster está ativo e online
            - ✓ Confirme o nome exato do database e coleção
            - ✓ Teste a conexão diretamente no MongoDB Compass
            """)

# Rodapé
st.markdown("---")
st.caption("🔒 Suas credenciais não são armazenadas e são usadas apenas durante a sessão atual.")