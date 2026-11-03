# Microsserviço de Enriquecimento de Leads B2B

Microsserviço desenvolvido para automatizar o fluxo de qualificação e inteligência comercial. A aplicação recebe dados brutos de leads, aplica validações estritas, consome a API do Google Gemini para gerar um dossiê executivo de vendas sob medida e persiste tudo de forma estruturada no Baserow.

O foco principal deste projeto foi garantir **resiliência e confiabilidade** — garantindo que falhas temporárias de rede ou picos de requisição na IA não derrubem o pipeline de vendas.

---

## O Problema que ele Resolve

Em operações comerciais, o tempo de resposta e a riqueza de contexto sobre o lead fazem toda a diferença. O desafio aqui era criar um componente leve (FastAPI) que fizesse o meio de campo entre ferramentas de automação (como n8n ou webhooks genéricos) e uma base de dados centralizada, adicionando inteligência artificial no meio do processo sem correr o risco de perder dados caso a API externa falhe.

---

## Arquitetura e Decisões Técnicas

* **FastAPI:** Escolhido pela alta performance assíncrona, documentação automática integrada (Swagger) e validação nativa baseada em tipagem.
* **Pydantic v2:** Utilizado para garantir a integridade dos dados de entrada (`EmailStr`, campos opcionais e estruturação rigorosa do payload).
* **Google GenAI SDK (`gemini-2.5-flash`):** Responsável por atuar como analista de inteligência comercial, estruturando os quatro pilares do dossiê (resumo da empresa, perfil de decisão, dores típicas e sugestão de abordagem).
* **Resiliência a Falhas (Retry & Fallback):** Como APIs de IA públicas estão sujeitas a picos de tráfego e erros `503 (Unavailable)`, implementei um mecanismo de repetição com intervalo controlado (`time.sleep`) e um modo *fallback* elegante. Se a IA estiver instável, a API entrega um dossiê estruturado padrão para que o pipeline de dados nunca sofra interrupções.
* **Docker & Docker Compose:** Todo o ambiente é containerizado, facilitando o deploy e a reproducibilidade em qualquer servidor.

---

## Estrutura do Repositório

```text
agente_leads_b2b/
├── main.py             # Núcleo da API, rotas, modelos e lógica de integração com IA
├── requirements.txt    # Dependências fixadas do projeto
├── Dockerfile          # Configuração da imagem do container Python
├── docker-compose.yml  # Orquestração do serviço
├── .env                # Variáveis de ambiente (ignorado pelo controle de versão)
└── .gitignore          # Regras de segurança para exclusão de segredos