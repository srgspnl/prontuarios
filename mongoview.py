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

# CSS customizado para melhorar a legibilidade
st.markdown("""
<style>
    .documento-card {
        background-color: #f8f9fa;
        border-left: 4px solid #4CAF50;
        padding: 20px;
        margin: 15px 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .documento-header {
        color: #2c3e50;
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #e0e0e0;
    }
    .campo-chave {
        color: #2980b9;
        font-weight: 600;
        display: inline-block;
        min-width: 200px;
    }
    .campo-valor {
        color: #34495e;
        word-wrap: break-word;
    }
    .linha-campo {
        padding: 8px 0;
        border-bottom: 1px solid #ecf0f1;
    }
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

# ==================== FUNÇÃO DE RENDERIZAÇÃO ====================

def renderizar_documento_html(idx, dados_achatados):
    """Renderiza um documento de forma elegante em HTML"""
    doc_id = dados_achatados.get('_id.$oid', 'N/A')
    
    html = f"""
    <div class="documento-card">
        <div class="documento-header">
            📄 DOCUMENTO {idx + 1} 
            <span style="color: #7f8c8d; font-size: 0.85em; font-weight: normal;">
                (ID: {doc_id[:8]}...{doc_id[-8:] if len(doc_id) > 16 else doc_id})
            </span>
        </div>
    """
    
    for chave, valor in dados_achatados.items():
        # Limitar tamanho do valor para visualização
        valor_exibido = valor if len(str(valor)) <= 100 else str(valor)[:100] + "..."
        
        html += f"""
        <div class="linha-campo">
            <span class="campo-chave">{chave}:</span>
            <span class="campo-valor">{valor_exibido}</span>
        </div>
        """
    
    html += "</div>"
    return html

# ==================== FUNÇÃO DE EXTRAÇÃO ====================

def buscar_e_gerar_txt(mongo_uri, database_name, collection_name):
    """
    Conecta ao MongoDB e gera o conteúdo do relatório.
    Retorna (sucesso, conteudo_txt, documentos_processados, num_documentos)
    """
    client = None
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[database_name]
        collection = db[collection_name]
        client.server_info()
        
        documentos = list(collection.find())
        
        # Gerar conteúdo TXT
        output = io.StringIO()
        output.write(f"--- RELATÓRIO DE DOCUMENTOS MONGODB (Formato Achatado) ---\n")
        output.write(f"Data de Geração: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write("-" * 70 + "\n\n")
        
        docs_processados = []
        for idx, doc in enumerate(documentos):
            dados_achatados = normalizar_documento(doc)
            docs_processados.append(dados_achatados)
            
            output.write(f"== DOCUMENTO {idx + 1} ==")
            output.write(f" (ID: {dados_achatados.get('_id.$oid', 'N/A')})\n")
            
            for chave, valor in dados_achatados.items():
                output.write(f"{chave}: {valor}\n")
                
            output.write("-" * 70 + "\n\n")
        
        conteudo = output.getvalue()
        output.close()
        
        return True, conteudo, docs_processados, len(documentos)
        
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
        senha = st.text_input("Senha", type="password", help="Senha do usuário MongoDB")
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
    else:
        mongo_uri = f"mongodb+srv://{usuario}:{senha}@{host}/{database}?retryWrites=true&w=majority"
        
        with st.spinner("🔄 Conectando ao MongoDB e extraindo dados..."):
            sucesso, resultado_txt, docs_processados, num_docs = buscar_e_gerar_txt(mongo_uri, database, collection)
        
        if sucesso:
            st.success(f"✅ Conexão estabelecida com sucesso!")
            
            # Estatísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="stats-box">
                    <div class="stats-number">{num_docs}</div>
                    <div class="stats-label">Documentos</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                total_campos = sum(len(doc) for doc in docs_processados)
                st.markdown(f"""
                <div class="stats-box" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                    <div class="stats-number">{total_campos}</div>
                    <div class="stats-label">Campos Totais</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                timestamp = datetime.now().strftime('%H:%M:%S')
                st.markdown(f"""
                <div class="stats-box" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                    <div class="stats-number">{timestamp}</div>
                    <div class="stats-label">Hora da Extração</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Opções de visualização
            tab1, tab2 = st.tabs(["📱 Visualização Amigável", "📄 Formato Texto"])
            
            with tab1:
                st.markdown("### 📋 Documentos Extraídos")
                
                # Controle de paginação para muitos documentos
                docs_por_pagina = 5
                if num_docs > docs_por_pagina:
                    pagina = st.number_input(
                        "Página", 
                        min_value=1, 
                        max_value=(num_docs // docs_por_pagina) + 1,
                        value=1
                    )
                    inicio = (pagina - 1) * docs_por_pagina
                    fim = min(inicio + docs_por_pagina, num_docs)
                    docs_exibir = docs_processados[inicio:fim]
                    idx_offset = inicio
                else:
                    docs_exibir = docs_processados
                    idx_offset = 0
                
                # Renderizar documentos
                for idx, doc in enumerate(docs_exibir):
                    html_doc = renderizar_documento_html(idx + idx_offset, doc)
                    st.markdown(html_doc, unsafe_allow_html=True)
            
            with tab2:
                st.text_area("Conteúdo Completo", resultado_txt, height=500)
            
            # Botão de download
            st.markdown("---")
            st.download_button(
                label="📥 Download do Relatório Completo (.txt)",
                data=resultado_txt,
                file_name=f"relatorio_mongodb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
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