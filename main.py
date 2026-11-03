from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field 
from typing import Optional
from dotenv import load_dotenv  
from google import genai
import time
import requests
import os 

load_dotenv()

# --- CONFIGURAÇÕES DO BASEROW ---
BASEROW_TOKEN = os.getenv("BASEROW_TOKEN" )  # Cole aqui o seu token da API do Baserow
BASEROW_TABLE_ID = os.getenv("BASEROW_TABLE_ID")  # Cole aqui o ID numérico da sua tabela (ex: 2538813)
BASEROW_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_TABLE_ID}/?user_field_names=true"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None # Cole aqui o seu token da API do GEMINI

app = FastAPI(
    title="Microserviço de Enriquecimento de Leads B2B", 
    description="API desenvolvida em FastAPI para processamento e envio ao Baserow.",
    version="2.0"
)


class LeadInput(BaseModel):
    nome_completo: Optional[str] = Field(None, description="Nome do contato")
    lead_id: Optional[str] = Field(None, description="Identificador do lead")
    email_corporativo: Optional[EmailStr] = Field(None, description="E-mail profissional")
    cargo: Optional[str] = Field(None, description="Cargo do lead")
    empresa: Optional[str] = Field(None, description="Nome da empresa")
    telefone_tratado: Optional[str] = Field(None, description="Telefone formatado")
    dossie_vendas: Optional[str] = Field("Aguardando geração do dossiê via NotebookLM/IA", description="Dossiê de vendas")
    captura_de_dados: Optional[str] = Field(None, description="Dados capturados")

class LeadResponse(BaseModel):
    status: str 
    mensage: str
    dados_recebidos: LeadInput 

def gerar_dossie_de_vendas(nome_completo: str, cargo: str, empresa: str) -> str:
    """
    Gera um dossiê executivo de vendas dinâmico utilizando a IA real do Google Gemini.
    Caso a chave da API não esteja configurada, aplica um fallback seguro.
    """
    if not gemini_client:
        return (
            f"Resumo Executivo - {empresa}\n"
            f"Contato-chave: {nome_completo} ({cargo})\n"
            f"Perfil de Decisão: Foco em otimização de processos (Modo Fallback).\n\n" 
            f"Estratégia de Abordagem: Conduzir a demonstração enfatizando o ganho de produtividade operacional."
        )

    prompt = f"""
    Atue como um analista de inteligência comercial B2B experiente.
    Com base nos seguintes dados do lead:
    - Nome: {nome_completo}
    - Cargo: {cargo}
    - Empresa: {empresa}

    Gere um dossiê executivo de vendas sucinto, profissional e estruturado contendo exatamente estes 4 tópicos:
    1. Resumo executivo da empresa e setor provável
    2. Perfil de decisão do cargo
    3. Dores e oportunidades estratégicas típicas
    4. Sugestão de abordagem comercial personalizada
    """

    tentativas = 3
    for tentativa in range(tentativas):
        try:
            response = gemini_client.models.generate_content(
                 contents=prompt, 
                 model="gemini-2.5-flash"
           )

            return response.text.strip()
        except Exception as e:
            if "503" in str(e) and tentativa < tentativas - 1:
                 time.sleep(2)  # Aguarda antes de tentar novamente
                 continue

            if tentativa == tentativas - 1:
               return (
                   f"Resumo Executivo - {empresa}\n"
                   f"Contato-chave: {nome_completo} ({cargo})\n"
                   f"Perfil de Decisão: Foco em eficiência operacional (Modo Fallback por alta demanda).\n\n" 
                   f"Estratégia de Abordagem: Enfatizar o ganho de produtividade e agilidade."
                 )

@app.get("/", tags=["Status"])
def read_root():
    return {"status": "online", "servico": "Microserviço B2B FastAPI"}

@app.post("/api/v1/leads/processar", response_model=LeadResponse, status_code=status.HTTP_201_CREATED, tags=["Leads"])
def processar_lead(lead: LeadInput):
    """
    Recebe o lead, valida os dados e envia automaticamente para a tabela do Baserow.
    """
    try:
        # Gera o dossiê e atualiza o objeto 'lead' antes de enviar ao Baserow
        lead.dossie_vendas = gerar_dossie_de_vendas(
            empresa=lead.empresa or "Não informado",
            nome_completo=lead.nome_completo or "Não informado",
            cargo=lead.cargo or "Não informado",
            
        )

        headers = {
            "Authorization": f"Token {BASEROW_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Converte o modelo Pydantic para dicionário JSON
        payload = lead.model_dump(exclude_unset=True)

        # Envia a requisição POST para o Baserow
        response = requests.post(BASEROW_URL, json=payload, headers=headers)

        if response.status_code not in [200, 201]:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Erro ao salvar no Baserow: {response.text}"
            )

        return {
            "status": "sucesso",
            "mensage": "Lead recebido, validado e gravado no Baserow com sucesso!",
            "dados_recebidos": lead
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar o lead: {str(e)}"
        )