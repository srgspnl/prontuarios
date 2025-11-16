import streamlit as st
from web3 import Web3
import requests
import json
from datetime import datetime

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Verificador Blockchain",
    page_icon="🔍",
    layout="wide"
)

# ==================== CONSTANTES ====================
ALCHEMY_URL = "https://eth-sepolia.g.alchemy.com/v2/lda58Tw_56pU42krLOmDH"
CONTRACT_ADDRESS = "0xe363FEcb00805AE86bDA1071e681f66758Bc69F4"

CONTRACT_ABI = [
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "_hash",
                "type": "bytes32"
            }
        ],
        "name": "verifyHash",
        "outputs": [
            {
                "internalType": "bool",
                "name": "exists",
                "type": "bool"
            },
            {
                "internalType": "bool",
                "name": "isValid",
                "type": "bool"
            },
            {
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            },
            {
                "internalType": "address",
                "name": "provider",
                "type": "address"
            },
            {
                "internalType": "string",
                "name": "recordType",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "recordId",
                "type": "string"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# CSS customizado
st.markdown("""
<style>
    .verification-box-success {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .verification-box-warning {
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .verification-box-error {
        background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .hash-display {
        font-family: monospace;
        background-color: #f5f5f5;
        padding: 12px;
        border-radius: 8px;
        word-break: break-all;
        font-size: 0.9em;
    }
    .info-card {
        background-color: #f8f9fa;
        border-left: 4px solid #2196F3;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES ====================

def buscar_transacao_web3(w3, tx_hash):
    """
    Busca informações da transação via Web3 (Alchemy)
    """
    try:
        tx = w3.eth.get_transaction(tx_hash)
        return True, tx
    except Exception as e:
        return False, str(e)

def buscar_receipt_web3(w3, tx_hash):
    """
    Busca o receipt da transação via Web3 (Alchemy)
    """
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        return True, receipt
    except Exception as e:
        return False, str(e)

def verificar_hash_no_contrato(w3, contract, hash_hex):
    """
    Verifica o hash diretamente no smart contract
    """
    try:
        hash_bytes32 = w3.to_bytes(hexstr=hash_hex)
        exists, is_valid, timestamp, provider, record_type, record_id = \
            contract.functions.verifyHash(hash_bytes32).call()
        
        return {
            "exists": exists,
            "is_valid": is_valid,
            "timestamp": timestamp,
            "provider": provider,
            "record_type": record_type,
            "record_id": record_id
        }
    except Exception as e:
        return {"error": str(e)}

def extrair_hash_do_input_data(input_data):
    """
    Extrai o hash dos dados de input da transação
    O input começa com o function selector (4 bytes = 8 chars hex)
    seguido pelos parâmetros
    """
    try:
        # Input data já vem como HexBytes do Web3, converter para string
        if hasattr(input_data, 'hex'):
            input_data = input_data.hex()
        
        input_data = str(input_data)
        
        if input_data.startswith('0x'):
            input_data = input_data[2:]
        
        # Function selector: primeiros 8 caracteres (4 bytes)
        function_selector = input_data[:8]
        
        # Parâmetros: restante
        params = input_data[8:]
        
        # O primeiro parâmetro (hash) são os primeiros 64 caracteres (32 bytes)
        if len(params) >= 64:
            hash_from_input = params[:64]
            return hash_from_input
        
        return None
    except Exception as e:
        return None

# ==================== INTERFACE ====================

st.title("🔍 Verificador de Blockchain - Sepolia Testnet")
st.markdown("### Sistema de Verificação de Integridade Blockchain")
st.markdown("---")

# ==================== FORMULÁRIO ====================

with st.form("verification_form"):
    st.subheader("📝 Dados para Verificação")
    
    hash_documento = st.text_input(
        "Hash do Documento (SHA-256)",
        help="Hash SHA-256 de 64 caracteres hexadecimais",
        placeholder="5e74faa0e8b070ee34059b9a8a5f9173ae87d22b0c1940038f209bcee1aa0a5a"
    )
    
    tx_hash = st.text_input(
        "Transaction Hash (TX Hash)",
        help="Hash da transação no Sepolia (com ou sem 0x)",
        placeholder="0x1234567890abcdef..."
    )
    
    submit = st.form_submit_button("🔍 Verificar no Blockchain", use_container_width=True)

# ==================== PROCESSAMENTO ====================

if submit:
    if not hash_documento or not tx_hash:
        st.error("⚠️ Por favor, preencha ambos os campos.")
    else:
        # Normalizar hash do documento
        hash_documento = hash_documento.strip().lower()
        if hash_documento.startswith('0x'):
            hash_documento = hash_documento[2:]
        
        # Normalizar TX hash
        tx_hash = tx_hash.strip()
        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        
        # Validar comprimentos
        if len(hash_documento) != 64:
            st.error(f"❌ Hash do documento inválido. Deve ter 64 caracteres (tem {len(hash_documento)})")
            st.stop()
        
        if len(tx_hash) != 66:  # 0x + 64 chars
            st.error(f"❌ Transaction hash inválido. Deve ter 66 caracteres com 0x (tem {len(tx_hash)})")
            st.stop()
        
        st.markdown("---")
        
        # ==================== VERIFICAÇÃO 1: SMART CONTRACT ====================
        
        st.subheader("🔗 Verificação no Smart Contract")
        
        with st.spinner("Consultando smart contract no Sepolia..."):
            try:
                w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
                
                if not w3.is_connected():
                    st.error("❌ Não foi possível conectar à Sepolia Testnet")
                    st.stop()
                
                contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
                resultado_contrato = verificar_hash_no_contrato(w3, contract, hash_documento)
                
                if "error" in resultado_contrato:
                    st.error(f"❌ Erro ao consultar contrato: {resultado_contrato['error']}")
                elif resultado_contrato["exists"]:
                    st.success("✅ Hash encontrado no smart contract!")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        status = "🟢 VÁLIDO" if resultado_contrato["is_valid"] else "🔴 INVALIDADO"
                        st.metric("Status", status)
                    
                    with col2:
                        if resultado_contrato["timestamp"] > 0:
                            dt = datetime.fromtimestamp(resultado_contrato["timestamp"])
                            st.metric("Data de Registro", dt.strftime('%d/%m/%Y'))
                            st.caption(dt.strftime('%H:%M:%S'))
                        else:
                            st.metric("Data de Registro", "N/A")
                    
                    with col3:
                        st.metric("Provedor", resultado_contrato["provider"][:10] + "...")
                    
                    with st.expander("📋 Detalhes Completos do Contrato"):
                        st.json(resultado_contrato)
                else:
                    st.warning("⚠️ Hash NÃO encontrado no smart contract")
                    st.info("Isso pode significar que o hash nunca foi registrado ou foi registrado em outro contrato.")
                
            except Exception as e:
                st.error(f"❌ Erro ao verificar contrato: {e}")
                resultado_contrato = None
        
        # ==================== VERIFICAÇÃO 2: TRANSAÇÃO WEB3 ====================
        
        st.markdown("---")
        st.subheader("📡 Verificação da Transação (Web3)")
        
        with st.spinner("Buscando transação via Web3/Alchemy..."):
            sucesso_tx, dados_tx = buscar_transacao_web3(w3, tx_hash)
            
            if sucesso_tx:
                st.success("✅ Transação encontrada!")
                
                # Informações da transação
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Bloco", f"#{dados_tx['blockNumber']}")
                
                with col2:
                    st.metric("From", dados_tx['from'][:10] + "...")
                
                with col3:
                    st.metric("To (Contrato)", dados_tx['to'][:10] + "..." if dados_tx['to'] else "N/A")
                
                # Verificar input data
                input_data = dados_tx.get("input", "")
                hash_extraido = extrair_hash_do_input_data(input_data)
                
                if hash_extraido:
                    st.markdown("---")
                    st.subheader("🔐 Comparação de Hashes")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Hash do Documento (Informado):**")
                        st.code(hash_documento, language=None)
                    
                    with col2:
                        st.markdown("**Hash Extraído da Transação:**")
                        st.code(hash_extraido, language=None)
                    
                    # Comparar hashes
                    if hash_documento.lower() == hash_extraido.lower():
                        st.markdown("""
                        <div class="verification-box-success">
                            <h2 style="margin: 0;">✅ VERIFICAÇÃO COMPLETA</h2>
                            <p style="margin: 10px 0 0 0; font-size: 1.2em;">Os hashes correspondem perfeitamente!</p>
                            <p style="margin: 10px 0 0 0;">O hash do documento está registrado nesta transação blockchain</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="verification-box-warning">
                            <h2 style="margin: 0;">⚠️ HASHES DIFERENTES</h2>
                            <p style="margin: 10px 0 0 0; font-size: 1.2em;">Os hashes não correspondem</p>
                            <p style="margin: 10px 0 0 0;">O hash informado NÃO corresponde ao registrado nesta transação</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Não foi possível extrair o hash dos dados da transação")
                
                # Mostrar input data completo
                with st.expander("🔍 Ver Input Data Completo"):
                    if hasattr(input_data, 'hex'):
                        st.code(input_data.hex(), language=None)
                    else:
                        st.code(str(input_data), language=None)
                
            else:
                st.error(f"❌ Transação não encontrada: {dados_tx}")
        
        # Buscar receipt
        with st.spinner("Buscando receipt da transação..."):
            sucesso_receipt, dados_receipt = buscar_receipt_web3(w3, tx_hash)
            
            if sucesso_receipt:
                status = dados_receipt.get("status", 0)
                
                if status == 1:
                    st.success("✅ Transação confirmada com sucesso")
                else:
                    st.error("❌ Transação falhou ou foi revertida")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    gas_used = dados_receipt.get("gasUsed", 0)
                    st.metric("Gas Usado", f"{gas_used:,}")
                
                with col2:
                    st.metric("Status", "✅ Sucesso" if status == 1 else "❌ Falhou")
        
        # ==================== RESUMO FINAL ====================
        
        st.markdown("---")
        st.subheader("📊 Resumo da Verificação")
        
        # Determinar resultado final
        hash_no_contrato = resultado_contrato and resultado_contrato.get("exists", False)
        hash_na_transacao = sucesso_tx and hash_extraido and (hash_documento.lower() == hash_extraido.lower())
        
        if hash_no_contrato and hash_na_transacao:
            st.markdown("""
            <div class="info-card" style="border-left-color: #4CAF50;">
                <h4>🎉 Verificação Completa e Bem-Sucedida</h4>
                <ul>
                    <li>✅ Hash encontrado no smart contract</li>
                    <li>✅ Hash confirmado na transação blockchain</li>
                    <li>✅ Hashes correspondem perfeitamente</li>
                    <li>✅ Documento autêntico e não adulterado</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif hash_no_contrato and not hash_na_transacao:
            st.markdown("""
            <div class="info-card" style="border-left-color: #FF9800;">
                <h4>⚠️ Verificação Parcial</h4>
                <ul>
                    <li>✅ Hash encontrado no smart contract</li>
                    <li>❌ Hash não corresponde à transação informada</li>
                    <li>💡 O hash pode ter sido registrado em outra transação</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        elif not hash_no_contrato and hash_na_transacao:
            st.markdown("""
            <div class="info-card" style="border-left-color: #FF9800;">
                <h4>⚠️ Situação Inconsistente</h4>
                <ul>
                    <li>❌ Hash NÃO encontrado no smart contract</li>
                    <li>✅ Hash presente na transação</li>
                    <li>⚠️ A transação pode ter falhado ou sido revertida</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="info-card" style="border-left-color: #f44336;">
                <h4>❌ Verificação Falhou</h4>
                <ul>
                    <li>❌ Hash NÃO encontrado no smart contract</li>
                    <li>❌ Hash não corresponde à transação</li>
                    <li>⚠️ Verifique se os dados informados estão corretos</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Link para Etherscan
        st.markdown("---")
        st.link_button(
            "🔗 Ver Transação Completa no Etherscan",
            f"https://sepolia.etherscan.io/tx/{tx_hash}",
            use_container_width=True
        )

# ==================== INSTRUÇÕES ====================

st.markdown("---")

with st.expander("ℹ️ Como Usar Este Verificador"):
    st.markdown("""
    ### 🎯 Objetivo
    
    Este sistema verifica se um hash de documento está realmente registrado no blockchain Sepolia,
    fazendo uma verificação dupla usando apenas Web3/Alchemy (sem necessidade de API key externa):
    
    1. **No Smart Contract**: Consulta diretamente o contrato para ver se o hash existe
    2. **Na Transação**: Analisa os dados da transação para confirmar que o hash foi enviado
    
    ### 📝 Como Usar
    
    1. **Hash do Documento**: Cole o hash SHA-256 (64 caracteres) do documento
    2. **Transaction Hash**: Cole o hash da transação blockchain (66 caracteres com 0x)
    3. Clique em "Verificar no Blockchain"
    
    ### ✅ Resultados Possíveis
    
    - **🟢 Verificação Completa**: Hash encontrado no contrato E na transação
    - **🟡 Verificação Parcial**: Hash apenas no contrato OU apenas na transação
    - **🔴 Verificação Falhou**: Hash não encontrado
    
    ### 💡 Onde Encontrar os Dados
    
    - **Hash do Documento**: Campo `blockchain_info.document_hash` no MongoDB
    - **Transaction Hash**: Campo `blockchain_info.transaction.transaction_hash` no MongoDB
    - Ou use o sistema de visualização de documentos para copiar os valores
    """)

# ==================== RODAPÉ ====================

st.markdown("---")
st.caption("🔗 Verificador Blockchain - Sepolia Testnet")
st.caption("🔍 Sistema de Verificação de Integridade e Autenticidade")