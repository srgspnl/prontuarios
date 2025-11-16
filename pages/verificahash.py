import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId
import hashlib
import json
from datetime import datetime

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Verificador de Integridade",
    page_icon="🔍",
    layout="wide"
)

# CSS customizado
st.markdown("""
<style>
    .integrity-box-valid {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .integrity-box-invalid {
        background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .integrity-box-none {
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .hash-display {
        font-family: monospace;
        font-size: 0.9em;
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 5px;
        word-break: break-all;
    }
</style>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES AUXILIARES ====================

def extrair_valores_para_hash(obj, valores=[]):
    """
    Extrai recursivamente apenas os VALORES (sem chaves, vírgulas, aspas, etc)
    de um objeto JSON para gerar hash consistente.
    """
    if isinstance(obj, dict):
        # Ordenar chaves para garantir consistência
        for key in sorted(obj.keys()):
            extrair_valores_para_hash(obj[key], valores)
    elif isinstance(obj, list):
        for item in obj:
            extrair_valores_para_hash(item, valores)
    else:
        # Converter valor para string e adicionar
        valores.append(str(obj))
    return valores

def gerar_hash_documento(documento):
    """
    Gera hash SHA-256 apenas dos valores do documento,
    ignorando formatação JSON (aspas, vírgulas, chaves, etc)
    """
    # Remover campos que não fazem parte do documento original
    doc_copy = documento.copy()
    if '_id' in doc_copy:
        del doc_copy['_id']
    if 'blockchain_info' in doc_copy:
        del doc_copy['blockchain_info']
    
    # Extrair apenas valores
    valores = extrair_valores_para_hash(doc_copy)
    
    # Concatenar todos os valores
    valores_concatenados = ''.join(valores)
    
    # Gerar hash SHA-256
    hash_hex = hashlib.sha256(valores_concatenados.encode('utf-8')).hexdigest()
    
    return hash_hex, valores_concatenados

def verificar_integridade_documento(documento):
    """
    Verifica se o hash armazenado no blockchain_info corresponde
    ao conteúdo atual do documento (excluindo blockchain_info)
    """
    if 'blockchain_info' not in documento:
        return None, "Documento não possui informações de blockchain"
    
    hash_armazenado = documento.get('blockchain_info', {}).get('document_hash')
    
    if not hash_armazenado:
        return None, "Hash não encontrado em blockchain_info"
    
    # Calcular hash do documento atual (sem blockchain_info)
    hash_calculado, _ = gerar_hash_documento(documento)
    
    # Comparar
    if hash_armazenado == hash_calculado:
        return True, "Documento íntegro - hash corresponde ao conteúdo"
    else:
        return False, "Documento modificado - hash não corresponde"

# ==================== INTERFACE STREAMLIT ====================

st.title("🔍 Verificador de Integridade de Documentos")
st.markdown("### Sistema de Verificação de Hash - MongoDB")
st.markdown("---")

# ==================== CONEXÃO MONGODB ====================

if 'mongodb_connected' not in st.session_state:
    st.session_state.mongodb_connected = False
    st.session_state.documento = None

if not st.session_state.mongodb_connected:
    st.subheader("📊 Conectar ao MongoDB")
    
    with st.form("mongodb_credentials"):
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
        
        object_id_input = st.text_input(
            "ObjectId (_id) do Documento",
            help="Digite o _id do documento que será verificado"
        )
        
        submit_mongo = st.form_submit_button("🔌 Conectar e Buscar Documento", use_container_width=True)
    
    if submit_mongo:
        if not senha_mongodb:
            st.error("⚠️ Por favor, informe a senha do MongoDB.")
        elif len(senha_mongodb) < 12:
            st.error("⚠️ A senha deve ter exatamente 12 caracteres.")
        elif not object_id_input:
            st.error("⚠️ Por favor, informe o ObjectId do documento.")
        else:
            # Usar apenas os 8 primeiros caracteres da senha
            senha_utilizada = senha_mongodb[:8]
            mongo_uri = f"mongodb+srv://{usuario}:{senha_utilizada}@{host}/{database}?retryWrites=true&w=majority"
            
            try:
                with st.spinner("🔄 Conectando ao MongoDB..."):
                    mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                    db = mongo_client[database]
                    coll = db[collection]
                    mongo_client.server_info()
                    
                    # Buscar documento
                    object_id = ObjectId(object_id_input)
                    documento = coll.find_one({"_id": object_id})
                    
                    if not documento:
                        st.error(f"❌ Documento com _id '{object_id_input}' não encontrado!")
                        mongo_client.close()
                    else:
                        st.session_state.mongodb_connected = True
                        st.session_state.documento = documento
                        st.session_state.object_id = object_id
                        st.session_state.mongo_client = mongo_client
                        st.session_state.database_name = database
                        st.session_state.collection_name = collection
                        st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Erro ao conectar: {e}")

# ==================== VISUALIZAÇÃO E VERIFICAÇÃO ====================

if st.session_state.mongodb_connected:
    st.success("✅ Conectado ao MongoDB com sucesso!")
    
    documento = st.session_state.documento
    object_id = st.session_state.object_id
    
    # Verificar se documento tem blockchain_info
    tem_blockchain = 'blockchain_info' in documento
    
    # ==================== INFORMAÇÕES DO DOCUMENTO ====================
    
    st.subheader("📄 Documento Encontrado")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ObjectId", str(object_id)[:12] + "...")
    with col2:
        st.metric("ID Atendimento", documento.get('idAtendimento', 'N/A'))
    with col3:
        st.metric("CNS Paciente", documento.get('cnsPaciente', 'N/A')[:12] + "..." if documento.get('cnsPaciente') else 'N/A')
    
    # ==================== VERIFICAÇÃO DE INTEGRIDADE ====================
    
    st.markdown("---")
    st.subheader("🔍 Verificação de Integridade")
    
    if tem_blockchain:
        integro, mensagem = verificar_integridade_documento(documento)
        
        if integro is True:
            st.markdown("""
            <div class="integrity-box-valid">
                <h2 style="margin: 0;">✅ DOCUMENTO ÍNTEGRO</h2>
                <p style="margin: 10px 0 0 0; font-size: 1.1em;">O hash corresponde ao conteúdo original</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Informações do blockchain
            blockchain_info = documento.get('blockchain_info', {})
            hash_armazenado = blockchain_info.get("document_hash", "N/A")
            hash_calculado, _ = gerar_hash_documento(documento)
            
            # Limpar espaços e normalizar
            hash_armazenado_limpo = hash_armazenado.strip().lower()
            hash_calculado_limpo = hash_calculado.strip().lower()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Hash Armazenado")
                st.code(hash_armazenado_limpo, language=None)
                st.caption(f"Tamanho: {len(hash_armazenado_limpo)} caracteres")
                
            with col2:
                st.markdown("#### 🔐 Hash Calculado")
                st.code(hash_calculado_limpo, language=None)
                st.caption(f"Tamanho: {len(hash_calculado_limpo)} caracteres")
            
            st.success("✅ Os hashes são idênticos - documento não foi alterado")
            
            # Debug adicional
            with st.expander("🔬 Análise Detalhada dos Hashes"):
                st.write("**Comparação caractere por caractere:**")
                st.write(f"- Hash armazenado == Hash calculado: **{hash_armazenado_limpo == hash_calculado_limpo}**")
                st.write(f"- Comprimento armazenado: {len(hash_armazenado_limpo)}")
                st.write(f"- Comprimento calculado: {len(hash_calculado_limpo)}")
                
                if hash_armazenado_limpo != hash_calculado_limpo:
                    st.error("⚠️ ATENÇÃO: Hashes diferentes detectados!")
                    st.write("**Hash Armazenado (hex):**")
                    st.code(hash_armazenado_limpo)
                    st.write("**Hash Calculado (hex):**")
                    st.code(hash_calculado_limpo)
            
        elif integro is False:
            st.markdown("""
            <div class="integrity-box-invalid">
                <h2 style="margin: 0;">⚠️ DOCUMENTO MODIFICADO</h2>
                <p style="margin: 10px 0 0 0; font-size: 1.1em;">O conteúdo foi alterado após o registro</p>
            </div>
            """, unsafe_allow_html=True)
            
            blockchain_info = documento.get('blockchain_info', {})
            hash_armazenado = blockchain_info.get('document_hash', 'N/A')
            hash_calculado, _ = gerar_hash_documento(documento)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Hash Armazenado (Original)")
                st.markdown(f'<div class="hash-display">{hash_armazenado}</div>', unsafe_allow_html=True)
                
            with col2:
                st.markdown("#### 🔐 Hash Calculado (Atual)")
                st.markdown(f'<div class="hash-display">{hash_calculado}</div>', unsafe_allow_html=True)
            
            st.error("❌ Os hashes são diferentes - documento foi modificado após o registro blockchain")
            
        else:
            st.warning(mensagem)
        
        # Detalhes do registro blockchain
        st.markdown("---")
        st.subheader("📋 Informações do Registro Blockchain")
        
        blockchain_info = documento.get('blockchain_info', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            registered_at = blockchain_info.get('registered_at', 'N/A')
            if registered_at != 'N/A':
                try:
                    dt = datetime.fromisoformat(registered_at)
                    st.metric("Data de Registro", dt.strftime('%d/%m/%Y'))
                    st.caption(dt.strftime('%H:%M:%S'))
                except:
                    st.metric("Data de Registro", registered_at[:10] if len(registered_at) > 10 else registered_at)
            else:
                st.metric("Data de Registro", 'N/A')
        
        with col2:
            tx_hash = blockchain_info.get('transaction', {}).get('transaction_hash', 'N/A')
            if tx_hash != 'N/A':
                st.metric("TX Hash", tx_hash[:8] + "...")
            else:
                st.metric("TX Hash", 'N/A')
        
        with col3:
            block_number = blockchain_info.get('transaction', {}).get('block_number', 'N/A')
            st.metric("Bloco", f"#{block_number}" if block_number != 'N/A' else 'N/A')
        
        with col4:
            network = blockchain_info.get('network', 'N/A')
            st.metric("Rede", network)
        
        # Expandable com detalhes completos
        with st.expander("🔍 Ver Detalhes Completos do Blockchain"):
            st.json(blockchain_info)
        
        # Link para Etherscan
        etherscan_url = blockchain_info.get('etherscan_url')
        if etherscan_url:
            st.link_button("🔗 Ver Transação no Etherscan", etherscan_url, use_container_width=True)
    
    else:
        st.markdown("""
        <div class="integrity-box-none">
            <h2 style="margin: 0;">📄 SEM REGISTRO BLOCKCHAIN</h2>
            <p style="margin: 10px 0 0 0; font-size: 1.1em;">Este documento não possui informações de blockchain</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("💡 Este documento ainda não foi registrado no blockchain, portanto não há hash para verificar.")
        
        # Mostrar hash que seria gerado
        st.markdown("---")
        st.subheader("🔐 Hash do Documento Atual")
        
        hash_calculado, valores_concatenados = gerar_hash_documento(documento)
        
        st.markdown(f'<div class="hash-display">{hash_calculado}</div>', unsafe_allow_html=True)
        st.caption(f"📊 Calculado a partir de {len(valores_concatenados)} caracteres")
        
        with st.expander("🔍 Ver Valores Concatenados (Base do Hash)"):
            st.text_area(
                "Valores extraídos do JSON", 
                valores_concatenados[:2000] + "..." if len(valores_concatenados) > 2000 else valores_concatenados, 
                height=300
            )
    
    # ==================== DOCUMENTO COMPLETO ====================
    
    st.markdown("---")
    with st.expander("📄 Ver Documento Completo (JSON)", expanded=False):
        doc_json = json.loads(json.dumps(documento, default=str, indent=2, ensure_ascii=False))
        st.json(doc_json)
    
    # ==================== BOTÃO PARA VERIFICAR OUTRO ====================
    
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Verificar Outro Documento", use_container_width=True):
            st.session_state.mongodb_connected = False
            st.session_state.mongo_client.close()
            st.rerun()

# ==================== RODAPÉ ====================

st.markdown("---")
st.caption("🔒 Sistema de Verificação de Integridade - Apenas leitura (não interage com blockchain)")
st.caption("💡 Este sistema verifica se o documento foi alterado comparando o hash armazenado com o hash calculado do conteúdo atual")