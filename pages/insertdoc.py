import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import json

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Upload Documento MongoDB",
    page_icon="📤",
    layout="centered"
)

# CSS customizado
st.markdown("""
<style>
    .success-box {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .objectid-display {
        font-family: monospace;
        font-size: 1.3em;
        background-color: rgba(255,255,255,0.2);
        padding: 15px;
        border-radius: 8px;
        margin-top: 15px;
        word-break: break-all;
    }
</style>
""", unsafe_allow_html=True)

# ==================== INTERFACE ====================

st.title("📤 Upload de Documento para MongoDB")
st.markdown("### Sistema de Inserção de Registros JSON")
st.markdown("---")

# ==================== FORMULÁRIO ====================

with st.form("upload_form"):
    st.subheader("🔐 Credenciais do MongoDB")
    
    col1, col2 = st.columns(2)
    
    with col1:
        usuario = st.text_input("Usuário", value="admin")
        database = st.text_input("Database", value="context")
    
    with col2:
        senha_mongodb = st.text_input(
            "Senha MongoDB", 
            type="password",
            help="Digite 12 caracteres (apenas os 8 primeiros serão usados)"
        )
        collection = st.text_input("Coleção", value="SaudeTeste")
    
    host = st.text_input(
        "Host/Cluster",
        value="cluster0.rfdha.gcp.mongodb.net"
    )
    
    st.markdown("---")
    st.subheader("📄 Arquivo JSON")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo JSON",
        type=['json', 'txt'],
        help="Arquivo deve conter um único objeto JSON válido"
    )
    
    # Prévia do arquivo
    if uploaded_file is not None:
        try:
            # Ler conteúdo do arquivo
            file_content = uploaded_file.read().decode('utf-8')
            documento = json.loads(file_content)
            
            # Verificar se é um dicionário
            if not isinstance(documento, dict):
                st.error("❌ O arquivo deve conter um único objeto JSON (não uma lista ou outro tipo)")
            else:
                st.success(f"✅ Arquivo válido! {len(documento)} campos encontrados")
                
                # Mostrar preview
                with st.expander("👁️ Prévia do Documento"):
                    st.json(documento)
                
                # Resetar ponteiro do arquivo
                uploaded_file.seek(0)
                
        except json.JSONDecodeError as e:
            st.error(f"❌ Erro ao processar JSON: {e}")
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo: {e}")
    
    submit = st.form_submit_button("🚀 Inserir no MongoDB", use_container_width=True)

# ==================== PROCESSAMENTO ====================

if submit:
    # Validações
    if not senha_mongodb:
        st.error("⚠️ Por favor, informe a senha do MongoDB.")
    elif len(senha_mongodb) < 12:
        st.error("⚠️ A senha deve ter exatamente 12 caracteres.")
    elif uploaded_file is None:
        st.error("⚠️ Por favor, selecione um arquivo JSON.")
    else:
        try:
            # Ler e validar JSON
            file_content = uploaded_file.read().decode('utf-8')
            documento = json.loads(file_content)
            
            if not isinstance(documento, dict):
                st.error("❌ O arquivo deve conter um único objeto JSON (dicionário).")
                st.stop()
            
            # Usar apenas os 8 primeiros caracteres da senha
            senha_utilizada = senha_mongodb[:8]
            mongo_uri = f"mongodb+srv://{usuario}:{senha_utilizada}@{host}/{database}?retryWrites=true&w=majority"
            
            # Conectar ao MongoDB
            with st.spinner("🔄 Conectando ao MongoDB..."):
                client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                
                # Testar conexão
                client.admin.command('ping')
                st.success("✅ Conexão estabelecida com MongoDB!")
                
                # Selecionar database e coleção
                db = client[database]
                coll = db[collection]
                
                # Inserir documento
                with st.spinner("📝 Inserindo documento..."):
                    result = coll.insert_one(documento)
                    object_id = result.inserted_id
                
                # Fechar conexão
                client.close()
            
            # Exibir sucesso
            st.markdown("---")
            st.markdown("""
            <div class="success-box">
                <h2 style="margin: 0;">✅ DOCUMENTO INSERIDO COM SUCESSO!</h2>
                <p style="margin: 10px 0; font-size: 1.1em;">O registro foi adicionado à coleção</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Informações do registro
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Database", database)
            with col2:
                st.metric("Coleção", collection)
            with col3:
                st.metric("Campos", len(documento))
            
            # Exibir ObjectId
            st.markdown("---")
            st.subheader("🆔 ObjectId Gerado")
            st.code(str(object_id), language=None)
            
            st.info("💡 Use este ObjectId para consultar, atualizar ou registrar o documento no blockchain")
            
            # Mostrar documento inserido
            with st.expander("📄 Ver Documento Inserido"):
                documento_completo = documento.copy()
                documento_completo['_id'] = str(object_id)
                st.json(documento_completo)
            
            st.balloons()
            
        except ConnectionFailure:
            st.error("❌ Falha ao conectar ao MongoDB. Verifique suas credenciais e conexão de rede.")
        except json.JSONDecodeError as e:
            st.error(f"❌ Erro ao processar JSON: {e}")
        except Exception as e:
            st.error(f"❌ Erro inesperado: {e}")
            st.info("💡 Verifique se:\n- A senha está correta\n- O banco de dados existe\n- Você tem permissão de escrita na coleção")

# ==================== INSTRUÇÕES ====================

st.markdown("---")

with st.expander("ℹ️ Instruções de Uso"):
    st.markdown("""
    ### Como usar este sistema:
    
    1. **Preencha as credenciais do MongoDB**
       - Usuário (padrão: admin)
       - Senha com 12 caracteres (apenas os 8 primeiros serão usados)
       - Database e Coleção de destino
    
    2. **Faça upload do arquivo JSON**
       - Formato: `.json` ou `.txt`
       - Conteúdo: Um único objeto JSON válido
       - Exemplo:
       ```json
       {
           "idAtendimento": "ATD001",
           "cnsPaciente": "123456789",
           "tipoAtendimento": "consulta",
           "dataHoraAtendimento": "2024-01-15T10:30:00"
       }
       ```
    
    3. **Clique em "Inserir no MongoDB"**
       - O sistema validará o JSON
       - Conectará ao MongoDB
       - Inserirá o documento
       - Retornará o ObjectId gerado
    
    4. **Guarde o ObjectId**
       - Use-o para registrar no blockchain posteriormente
       - Use-o para consultas e verificações
    
    ### ⚠️ Observações:
    - Cada upload cria um **novo documento** no MongoDB
    - O ObjectId (_id) é gerado automaticamente pelo MongoDB
    - Não há verificação de duplicatas
    - O hash será gerado apenas no momento do registro blockchain
    """)

# ==================== RODAPÉ ====================

st.markdown("---")
st.caption("🔒 Suas credenciais não são armazenadas e são usadas apenas durante a sessão atual")
st.caption("📤 Sistema de Upload - MongoDB Atlas")