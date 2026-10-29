 <h1 align="center">💊 Farma Aura</h1>

<p align="center">
  <strong>Pesquisa inteligente e comparação de preços de medicamentos com Python, LangChain e LangGraph</strong>
</p>

<p align="center">
  <a href="#sobre-o-projeto">Sobre o projeto</a> •
  <a href="#tecnologias">Tecnologias</a> •
  <a href="#practices-adopted">Práticas adotadas</a> •
  <a href="#pre-requisites">Requisitos</a> •
  <a href="#how-to-installing">Instalando o projeto</a> •
  <a href="#how-to-use">Como executar</a> •
  <a href="#security">Segurança</a> •
  <a href="#deploy">Deploy</a>
</p>

<p align="center">
  <a href="https://github.com/anacmenezes/farma_aura">
    <img src="https://img.shields.io/badge/GitHub-Projeto-black?logo=github" alt="GitHub">
  </a>
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white" alt="Python 3.13">
  <img src="https://img.shields.io/badge/LangChain-Framework-1C3C3C" alt="LangChain">
  <img src="https://img.shields.io/badge/LangGraph-Agents-1C3C3C" alt="LangGraph">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/Deploy-Azure-0078D4?logo=microsoftazure&logoColor=white" alt="Azure">
  <img src="https://img.shields.io/badge/Status-Em%20desenvolvimento-orange" alt="Status: em desenvolvimento">
</p>

<h2 id="sobre-o-projeto">📌 Sobre o projeto</h2>

<p>
O <strong>Farma Aura</strong> é uma aplicação desenvolvida em Python para pesquisar e comparar preços de medicamentos em catálogos de farmácias online. A aplicação utiliza agentes de Inteligência Artificial para interpretar solicitações, coordenar a pesquisa de produtos e apresentar os resultados de forma organizada.
</p>

<p>
A arquitetura combina LangChain e LangGraph para orquestração dos agentes, Streamlit para a interface web e FastAPI para disponibilizar operações de gerenciamento do catálogo de produtos. O sistema utiliza PostgreSQL para persistência e Docker para empacotamento dos serviços.
</p>

<p>
A aplicação está publicada no Azure Container Apps, com interface e API executadas em serviços separados.
</p>

<p align="center">
  <a href="https://farma-aura-streamlit.ashysky-801299e3.brazilsouth.azurecontainerapps.io">
    <img src="https://img.shields.io/badge/Acessar-Farma%20Aura-2E8B57?style=for-the-badge" alt="Acessar Farma Aura">
  </a>
</p>

<h3>Funcionalidades implementadas</h3>

<ul>
  <li>Interface web interativa com Streamlit.</li>
  <li>Pesquisa de medicamentos por solicitação em linguagem natural.</li>
  <li>Integração com catálogos de diferentes redes de farmácias.</li>
  <li>Comparação e organização das ofertas encontradas.</li>
  <li>Informação de CEP para contextualizar a pesquisa.</li>
  <li>Agente de pesquisa com ferramenta de busca de produtos.</li>
  <li>Agente de resposta para organizar os resultados obtidos.</li>
  <li>Orquestração do fluxo com LangGraph.</li>
  <li>API REST com operações CRUD para produtos.</li>
  <li>Persistência de dados com PostgreSQL e SQLAlchemy.</li>
  <li>Execução local com Docker Compose.</li>
  <li>Deploy da interface e do backend no Azure Container Apps.</li>
</ul>

<h3>Farmácias configuradas</h3>

<ul>
  <li>Pague Menos</li>
  <li>Drogaria São Paulo</li>
  <li>Drogarias Pacheco</li>
  <li>Drogarias Tamoio</li>
  <li>Drogaria Venancio</li>
  <li>Droga Raia</li>
  <li>Drogasil</li>
</ul>

<p><strong>Observação:</strong> a configuração de uma farmácia não garante que todos os produtos estejam disponíveis em todas as pesquisas. Os resultados dependem da resposta dos catálogos e da disponibilidade das integrações.</p>

<h2 id="tecnologias">🔌 Tecnologias</h2>

<ul>
  <li><a href="https://www.python.org/">Python</a> — linguagem principal.</li>
  <li><a href="https://www.langchain.com/">LangChain</a> — integração com modelos de linguagem e ferramentas.</li>
  <li><a href="https://www.langchain.com/langgraph">LangGraph</a> — orquestração do fluxo de agentes.</li>
  <li><a href="https://platform.openai.com/docs/">OpenAI API</a> — modelo de linguagem utilizado pelos agentes.</li>
  <li><a href="https://fastapi.tiangolo.com/">FastAPI</a> — construção da API REST.</li>
  <li><a href="https://streamlit.io/">Streamlit</a> — interface web.</li>
  <li><a href="https://www.postgresql.org/">PostgreSQL</a> — banco de dados relacional.</li>
  <li><a href="https://www.sqlalchemy.org/">SQLAlchemy</a> — ORM e acesso ao banco de dados.</li>
  <li><a href="https://docs.pydantic.dev/">Pydantic</a> — validação de dados.</li>
  <li><a href="https://requests.readthedocs.io/">Requests</a> — comunicação HTTP com a API.</li>
  <li><a href="https://www.docker.com/">Docker e Docker Compose</a> — containerização e execução dos serviços.</li>
  <li><a href="https://azure.microsoft.com/products/container-apps">Azure Container Apps</a> — hospedagem dos serviços.</li>
  <li><a href="https://azure.microsoft.com/products/container-registry">Azure Container Registry</a> — armazenamento de imagens Docker.</li>
</ul>

<h2 id="practices-adopted">📖 Práticas adotadas</h2>

<ul>
  <li>Separação entre interface, API, serviços de negócio, agentes e conectores.</li>
  <li>Orquestração de etapas de pesquisa e resposta com LangGraph.</li>
  <li>Uso de ferramentas para executar pesquisas reais nos catálogos configurados.</li>
  <li>Separação entre obtenção dos resultados e redação da resposta final.</li>
  <li>Validação de dados e organização de operações por meio de schemas.</li>
  <li>Persistência de dados em banco relacional.</li>
  <li>Configuração por variáveis de ambiente.</li>
  <li>Uso de segredos para credenciais na nuvem.</li>
  <li>Containerização dos serviços para facilitar a implantação.</li>
  <li>Deploy com interface e API independentes no Azure Container Apps.</li>
  <li>Tratamento de falhas e possibilidade de resultados parciais nas pesquisas.</li>
  <li>Desenvolvimento incremental com foco em modularidade e manutenção.</li>
</ul>

<h2 id="pre-requisites">💻 Requisitos</h2>

<p>Para executar o projeto localmente, são necessários:</p>

<ul>
  <li>Python 3.13 ou versão compatível com as dependências.</li>
  <li>Docker Desktop e Docker Compose, para execução containerizada.</li>
  <li>Chave de API da OpenAI com acesso ao modelo configurado.</li>
  <li>PostgreSQL, caso o banco seja executado fora do Docker Compose.</li>
  <li>Dependências listadas em <code>requirements.txt</code>.</li>
  <li>Acesso à internet para consultar os catálogos das farmácias.</li>
</ul>

<h2 id="how-to-installing">🚀 Instalando o projeto</h2>

<h3>1. Clone o repositório</h3>

<pre><code>git clone https://github.com/anacmenezes/farma_aura.git</code></pre>

<h3>2. Acesse a pasta</h3>

<pre><code>cd farma_aura</code></pre>

<h3>3. Crie um ambiente virtual</h3>

<pre><code>python -m venv .venv</code></pre>

<h3>4. Ative o ambiente virtual</h3>

<p>PowerShell (Windows):</p>

<pre><code>.\.venv\Scripts\Activate.ps1</code></pre>

<p>Linux ou macOS:</p>

<pre><code>source .venv/bin/activate</code></pre>

<h3>5. Instale as dependências</h3>

<pre><code>python -m pip install --upgrade pip
python -m pip install -r requirements.txt</code></pre>

<h3>6. Configure as variáveis de ambiente</h3>

<p>Crie um arquivo <code>.env</code> na raiz do projeto, utilizando <code>.env.example</code> como referência quando disponível.</p>

<pre><code>OPENAI_API_KEY=sua_chave_openai
OPENAI_MODEL=gpt-4o-mini

POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
POSTGRES_DB=farma_aura

DATABASE_URL=sua_url_de_conexao
DATABASE_URL_DOCKER=sua_url_de_conexao_docker

API_BASE_URL=http://127.0.0.1:8000</code></pre>

<p>Os valores de conexão devem seguir o formato esperado pela configuração do banco e pelo arquivo <code>docker-compose.yml</code>. Não publique credenciais reais no repositório.</p>

<h2 id="how-to-use">▶️ Como executar</h2>

<h3>Opção 1: Docker Compose</h3>

<p>Na raiz do projeto, execute:</p>

<pre><code>docker compose up --build</code></pre>

<p>Para executar em segundo plano:</p>

<pre><code>docker compose up --build -d</code></pre>

<h3>Opção 2: Execução local dos serviços</h3>

<p>Inicie a API FastAPI conforme o ponto de entrada definido no projeto. Na configuração atual, o comando utilizado pelo container da API é:</p>

<pre><code>uvicorn api.main:app --host 0.0.0.0 --port 8000</code></pre>

<p>Em outro terminal, inicie a interface Streamlit:</p>

<pre><code>streamlit run app.py</code></pre>

<p>Garanta que o PostgreSQL esteja acessível e que a variável <code>API_BASE_URL</code> aponte para o endereço da API.</p>

<h3>Acessando os serviços</h3>

<table>
  <thead>
    <tr>
      <th>Serviço</th>
      <th>Endereço local</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Streamlit</td>
      <td><code>http://localhost:8501</code></td>
    </tr>
    <tr>
      <td>FastAPI</td>
      <td><code>http://localhost:8000</code></td>
    </tr>
    <tr>
      <td>Swagger / OpenAPI</td>
      <td><code>http://localhost:8000/docs</code></td>
    </tr>
  </tbody>
</table>

<h3>Fluxo de utilização</h3>

<ol>
  <li>Acesse a interface do Farma Aura.</li>
  <li>Informe o medicamento que deseja pesquisar.</li>
  <li>Informe o CEP, quando aplicável.</li>
  <li>Execute a pesquisa.</li>
  <li>Consulte as ofertas retornadas e compare as informações disponíveis.</li>
</ol>

<h2 id="api">🔗 API REST</h2>

<p>A FastAPI disponibiliza endpoints para gerenciamento do catálogo de produtos.</p>

<table>
  <thead>
    <tr>
      <th>Método</th>
      <th>Endpoint</th>
      <th>Descrição</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>GET</td>
      <td><code>/health</code></td>
      <td>Verificação de saúde da API.</td>
    </tr>
    <tr>
      <td>GET</td>
      <td><code>/produtos</code></td>
      <td>Lista produtos cadastrados.</td>
    </tr>
    <tr>
      <td>POST</td>
      <td><code>/produtos</code></td>
      <td>Cadastra um produto.</td>
    </tr>
    <tr>
      <td>GET</td>
      <td><code>/produtos/{product_id}</code></td>
      <td>Consulta um produto.</td>
    </tr>
    <tr>
      <td>PATCH</td>
      <td><code>/produtos/{product_id}</code></td>
      <td>Atualiza um produto.</td>
    </tr>
    <tr>
      <td>DELETE</td>
      <td><code>/produtos/{product_id}</code></td>
      <td>Remove um produto.</td>
    </tr>
  </tbody>
</table>

<p>Com a API em execução, acesse <code>/docs</code> para consultar a documentação interativa.</p>

<h2 id="security">🔐 Segurança</h2>

<ul>
  <li>A chave da OpenAI deve ser armazenada em variável de ambiente ou em um gerenciador de segredos.</li>
  <li>Não publique arquivos <code>.env</code>, senhas, tokens ou strings de conexão com credenciais.</li>
  <li>Na Azure, utilize os segredos da Container App para configurar credenciais.</li>
  <li>O arquivo <code>.gitignore</code> deve excluir arquivos de ambiente, ambientes virtuais, caches e arquivos temporários.</li>
  <li>Não exponha gravações ou informações pessoais sem autorização.</li>
  <li>Trate os dados retornados por páginas externas como conteúdo não confiável.</li>
</ul>

<h2 id="deploy">☁️ Deploy</h2>

<p>O Farma Aura está publicado no Microsoft Azure, utilizando Azure Container Apps para hospedar a interface e o backend separadamente.</p>

<ul>
  <li><strong>Streamlit:</strong> interface web, publicada na porta 8501.</li>
  <li><strong>FastAPI:</strong> backend, publicado na porta 8000.</li>
  <li><strong>Azure Container Registry:</strong> armazenamento da imagem Docker.</li>
  <li><strong>PostgreSQL Flexible Server:</strong> banco de dados.</li>
  <li><strong>Azure Secrets:</strong> configuração protegida de credenciais.</li>
</ul>

<p><strong>Aplicação online:</strong> <a href="https://farma-aura-streamlit.ashysky-801299e3.brazilsouth.azurecontainerapps.io">Acessar Farma Aura</a></p>

<h2 id="author">👩‍💻 Ana Carulina Menezes</h2>

<p>
Projeto desenvolvido como parte do portfólio em <strong>Engenharia de IA</strong>, com foco em agentes inteligentes, integração com serviços externos, APIs, bancos de dados, containerização e implantação em nuvem.
</p>

<p align="center">
  <strong>Desenvolvido com Python, LangChain, LangGraph, FastAPI, Streamlit e Azure.</strong>
</p>
