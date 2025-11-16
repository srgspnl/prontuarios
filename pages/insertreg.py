import streamlit as st
from web3 import Web3
from pymongo import MongoClient
from bson.objectid import ObjectId
import hashlib
import json
from datetime import datetime

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Registro Blockchain",
    page_icon="🔗",
    layout="wide"
)

# ==================== CONSTANTES ====================
ALCHEMY_URL = "https://eth-sepolia.g.alchemy.com/v2/lda58Tw_56pU42krLOmDH"
CONTRACT_ADDRESS = "0xe363FEcb00805AE86bDA1071e681f66758Bc69F4"

CONTRACT_ABI = [
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "hash",
                "type": "bytes32"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "invalidatedBy",
                "type": "address"
            }
        ],
        "name": "HashInvalidated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "hash",
                "type": "bytes32"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "provider",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "recordType",
                "type": "string"
            },
            {
                "indexed": False,
                "internalType": "string",
                "name": "recordId",
                "type": "string"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256"
            }
        ],
        "name": "HashRegistered",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "provider",
                "type": "address"
            }
        ],
        "name": "ProviderAuthorized",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "provider",
                "type": "address"
            }
        ],
        "name": "ProviderRevoked",
        "type": "event"
    },
    {
        "inputs": [],
        "name": "admin",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_provider",
                "type": "address"
            }
        ],
        "name": "authorizeProvider",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "name": "authorizedProviders",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "_hash",
                "type": "bytes32"
            }
        ],
        "name": "invalidateHash",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_provider",
                "type": "address"
            }
        ],
        "name": "isProviderAuthorized",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "",
                "type": "bytes32"
            }
        ],
        "name": "records",
        "outputs": [
            {
                "internalType": "bytes32",
                "name": "documentHash",
                "type": "bytes32"
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
            },
            {
                "internalType": "bool",
                "name": "isValid",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "_hash",
                "type": "bytes32"
            },
            {
                "internalType": "string",
                "name": "_recordType",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "_recordId",
                "type": "string"
            }
        ],
        "name": "registerHash",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_provider",
                "type": "address"
            }
        ],
        "name": "revokeProvider",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_newAdmin",
                "type": "address"
            }
        ],
        "name": "transferAdmin",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
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
    # Remover campo _id para não afetar o hash
    doc_copy = documento.copy()
    if '_id' in doc_copy:
        del doc_copy['_id']
    
    # Extrair apenas valores
    valores = extrair_valores_para_hash(doc_copy)
    
    # Concatenar todos os valores
    valores_concatenados = ''.join(valores)
    
    # Gerar hash SHA-256
    hash_hex = hashlib.sha256(valores_concatenados.encode('utf-8')).hexdigest()
    
    return hash_hex, valores_concatenados

# ==================== INTERFACE STREAMLIT ====================

st.title("🔗 Registro de Documentos no Blockchain")
st.markdown("### Sistema de Registro Sepolia Testnet")
st.markdown("---")

# ==================== ETAPA 1: CREDENCIAIS MONGODB ====================

if 'mongodb_connected' not in st.session_state:
    st.session_state.mongodb_connected = False
    st.session_state.documento = None

if not st.session_state.mongodb_connected:
    st.subheader("📊 Etapa 1: Conectar ao MongoDB")
    
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
            help="Digite o _id do documento que será registrado no blockchain"
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
                        st.session_state.collection = coll
                        st.session_state.database_name = database
                        st.session_state.collection_name = collection
                        st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Erro ao conectar: {e}")

# ==================== ETAPA 2: VISUALIZAR E REGISTRAR ====================

if st.session_state.mongodb_connected:
    st.success("✅ Conectado ao MongoDB com sucesso!")
    
    documento = st.session_state.documento
    object_id = st.session_state.object_id
    
    # Mostrar informações do documento
    st.subheader("📄 Documento Encontrado")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ObjectId", str(object_id)[:12] + "...")
    with col2:
        st.metric("ID Atendimento", documento.get('idAtendimento', 'N/A'))
    with col3:
        st.metric("CNS Paciente", documento.get('cnsPaciente', 'N/A')[:12] + "...")
    
    # Mostrar JSON completo
    with st.expander("🔍 Ver Documento Completo (JSON)", expanded=False):
        doc_json = json.loads(json.dumps(documento, default=str, indent=2, ensure_ascii=False))
        st.json(doc_json)
    
    st.markdown("---")
    
    # Gerar hash do documento
    st.subheader("🔐 Hash do Documento")
    
    hash_hex, valores_concatenados = gerar_hash_documento(documento)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.code(hash_hex, language=None)
    with col2:
        st.info(f"📊 {len(valores_concatenados)} caracteres processados")
    
    with st.expander("🔍 Ver Valores Concatenados (Base do Hash)"):
        st.text_area("Valores extraídos do JSON", valores_concatenados[:1000] + "..." if len(valores_concatenados) > 1000 else valores_concatenados, height=200)
    
    st.markdown("---")
    
    # Formulário de registro no blockchain
    st.subheader("🔗 Etapa 2: Registrar no Blockchain")
    
    with st.form("blockchain_form"):
        st.markdown("**Credenciais da Carteira Ethereum**")
        
        private_key = st.text_input(
            "Chave Privada (sem 0x)",
            type="password",
            help="Sua chave privada da carteira Ethereum autorizada"
        )
        
        record_type = st.text_input(
            "Tipo de Registro",
            value=documento.get('tipoAtendimento', 'atendimento_saude'),
            help="Tipo do registro médico"
        )
        
        submit_blockchain = st.form_submit_button("🚀 Registrar no Blockchain Sepolia", use_container_width=True)
    
    if submit_blockchain:
        if not private_key:
            st.error("⚠️ Por favor, informe a chave privada.")
        else:
            try:
                # Conectar ao Web3
                with st.spinner("🔄 Conectando à Sepolia Testnet..."):
                    w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
                    
                    if not w3.is_connected():
                        st.error("❌ Não foi possível conectar à Sepolia!")
                        st.stop()
                    
                    st.success("✅ Conectado à Sepolia Testnet!")
                
                # Obter conta
                if private_key.startswith('0x'):
                    private_key = private_key[2:]
                
                account = w3.eth.account.from_key(private_key)
                st.info(f"👤 Conta: {account.address}")
                
                # Instanciar contrato
                contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
                
                # Verificar autorização
                with st.spinner("🔍 Verificando permissões..."):
                    is_authorized = contract.functions.isProviderAuthorized(account.address).call()
                    
                    if not is_authorized:
                        st.error("❌ Sua conta não está autorizada como provedor!")
                        st.info("💡 Apenas contas autorizadas podem registrar hashes no contrato.")
                        st.stop()
                    
                    st.success("✅ Conta autorizada como provedor!")
                
                # Registrar hash
                st.markdown("---")
                st.subheader("📝 Registrando Hash no Blockchain...")
                
                hash_bytes32 = w3.to_bytes(hexstr=hash_hex)
                record_id = str(object_id)
                
                with st.spinner("⏳ Enviando transação..."):
                    nonce = w3.eth.get_transaction_count(account.address)
                    
                    # Gas dinâmico
                    latest_block = w3.eth.get_block('latest')
                    base_fee = latest_block['baseFeePerGas']
                    max_priority_fee = w3.to_wei(2, 'gwei')
                    max_fee = base_fee * 2 + max_priority_fee
                    
                    transaction = contract.functions.registerHash(
                        hash_bytes32,
                        record_type,
                        record_id
                    ).build_transaction({
                        'from': account.address,
                        'nonce': nonce,
                        'gas': 300000,
                        'maxFeePerGas': max_fee,
                        'maxPriorityFeePerGas': max_priority_fee,
                    })
                    
                    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
                    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    tx_hash_hex = w3.to_hex(tx_hash)
                    
                    st.info(f"🔗 Transação enviada: {tx_hash_hex}")
                    st.link_button("🔍 Ver no Etherscan", f"https://sepolia.etherscan.io/tx/{tx_hash_hex}")
                    
                    # Aguardar confirmação
                    with st.spinner("⏳ Aguardando confirmação na blockchain..."):
                        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
                    
                    if tx_receipt.status == 1:
                        st.success("✅ HASH REGISTRADO COM SUCESSO!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Bloco", f"#{tx_receipt.blockNumber}")
                        with col2:
                            st.metric("Gas Usado", f"{tx_receipt.gasUsed:,}")
                        with col3:
                            st.metric("Status", "✅ Confirmado")
                        
                        # Verificar hash no blockchain
                        st.markdown("---")
                        st.subheader("🔍 Verificação no Blockchain")
                        
                        with st.spinner("Verificando hash registrado..."):
                            exists, is_valid, timestamp, provider, returned_type, returned_id = \
                                contract.functions.verifyHash(hash_bytes32).call()
                            
                            if exists:
                                date_time = datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')
                                
                                st.success("✅ Hash encontrado e verificado no blockchain!")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write("**Status:**", "🟢 VÁLIDO" if is_valid else "🔴 INVÁLIDO")
                                    st.write("**Data de Registro:**", date_time)
                                    st.write("**Provedor:**", provider)
                                with col2:
                                    st.write("**Tipo:**", returned_type)
                                    st.write("**Record ID:**", returned_id)
                                    st.write("**Integridade:**", "✅ OK" if returned_type == record_type and returned_id == record_id else "⚠️ Divergência")
                        
                        # Atualizar MongoDB
                        st.markdown("---")
                        st.subheader("💾 Atualizando MongoDB")
                        
                        blockchain_data = {
                            "blockchain_info": {
                                "document_hash": hash_hex,
                                "transaction": {
                                    "transaction_hash": tx_hash_hex,
                                    "block_number": tx_receipt.blockNumber,
                                    "gas_used": tx_receipt.gasUsed,
                                    "transaction_status": "success"
                                },
                                "verification": {
                                    "exists": exists,
                                    "is_valid": is_valid,
                                    "timestamp": timestamp,
                                    "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                                    "provider": provider,
                                    "record_type": returned_type,
                                    "record_id": returned_id
                                },
                                "contract_address": CONTRACT_ADDRESS,
                                "network": "Sepolia Testnet",
                                "registered_by": account.address,
                                "registered_at": datetime.now().isoformat(),
                                "etherscan_url": f"https://sepolia.etherscan.io/tx/{tx_hash_hex}"
                            }
                        }
                        
                        result = st.session_state.collection.update_one(
                            {"_id": object_id},
                            {"$set": blockchain_data}
                        )
                        
                        if result.modified_count > 0:
                            st.success("✅ Documento atualizado no MongoDB com informações da blockchain!")
                        
                        st.balloons()
                        
                    else:
                        st.error("❌ Transação falhou (revertida)")
                        
            except ValueError as e:
                if "Hash ja existe" in str(e) or "already exists" in str(e).lower():
                    st.warning("⚠️ Este hash já foi registrado anteriormente na blockchain!")
                else:
                    st.error(f"❌ Erro: {e}")
            except Exception as e:
                st.error(f"❌ Erro inesperado: {e}")
    
    # Botão para resetar
    st.markdown("---")
    if st.button("🔄 Registrar Outro Documento"):
        st.session_state.mongodb_connected = False
        st.session_state.mongo_client.close()

        st.rerun()
