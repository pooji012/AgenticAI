# MCP Demo

Two MCP servers built with **FastMCP** — a DateTime server (stdio) and a Jokes server (remote HTTP) — plus a **LangGraph agent** that connects to them via OpenAI.

---

## Project Structure

```
MCP Demo/
├── app.py            # DateTime MCP server (stdio transport)
├── jokes_mcp.py      # Jokes MCP server (HTTP transport)
├── agent.py          # LangGraph ReAct agent using the DateTime MCP
├── Dockerfile        # Docker image for the Jokes MCP server
├── requirements.txt  # Python dependencies
└── .env              # API keys (not committed)
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+ (for MCP Inspector)
- Docker (for container deployment)
- Azure CLI (for cloud deployment)

---

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
.venv\Scripts\activate           # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the template and add your OpenAI key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-...
```

---

## MCP Servers

### DateTime Server (`app.py`)

Runs over **stdio** transport. Provides 4 tools:

| Tool | Description |
|------|-------------|
| `get_current_time` | Current time in a given timezone |
| `get_current_date` | Current date in a given timezone |
| `get_current_datetime` | Date and time together |
| `list_timezones` | List timezones, optionally filtered by region |

```bash
python app.py
```

---

### Jokes Server (`jokes_mcp.py`)

Runs over **HTTP** transport on port `8000`. Provides 5 tools:

| Tool | Description |
|------|-------------|
| `get_random_joke` | Random joke from the collection |
| `get_joke_by_id` | Specific joke by ID (1–15) |
| `get_jokes_by_category` | All jokes in a category |
| `list_joke_categories` | Available categories and counts |
| `get_all_jokes` | Full joke list |

```bash
python jokes_mcp.py
```

Server starts at: `http://localhost:8000/mcp`

---

## MCP Inspector

The MCP Inspector is a browser UI for testing and exploring MCP servers.

### Install & Launch

```bash
npx @modelcontextprotocol/inspector
```

The inspector starts two services:

| Service | URL |
|---------|-----|
| Inspector UI | `http://localhost:6274` |
| Proxy server | `localhost:6277` |

The terminal output shows a **session token** — copy it:

```
🔑 Session token: abc123...
```

### Connect to the DateTime Server (stdio)

1. Open `http://localhost:6274`
2. Go to **Configuration** → paste the session token → Save
3. Set **Transport** to `STDIO`
4. Set **Command** to `python`
5. Set **Arguments** to the full path of `app.py`
6. Click **Connect**

### Connect to the Jokes Server (HTTP)

1. Open `http://localhost:6274`
2. Go to **Configuration** → paste the session token → Save
3. Set **Transport** to `Streamable HTTP`
4. Set **URL** to `http://localhost:8000/mcp`
5. Click **Connect**

### Connect to the Remote (Azure) Jokes Server

Same steps as HTTP, but use the remote URL:

```
http://jokes-mcp-server.eastus.azurecontainer.io:8000/mcp
```

---

## LangGraph Agent

The agent connects to the DateTime MCP server and uses OpenAI GPT-4o-mini to answer questions.

```bash
python agent.py
```

Example prompts:

```
You: What time is it in Tokyo?
You: What is today's date in New York?
You: List all timezones in Europe
You: exit
```

---

## Docker

### Build the image

```bash
docker build -t jokes-mcp .
```

### Run locally

```bash
docker run -d --name jokes-mcp -p 8000:8000 jokes-mcp
```

Server available at `http://localhost:8000/mcp`.

### Useful commands

```bash
docker logs jokes-mcp        # View logs
docker stop jokes-mcp        # Stop container
docker start jokes-mcp       # Start again
docker rm -f jokes-mcp       # Remove container
```

---

## Azure Deployment (ACI)

Deploy the Jokes server to **Azure Container Instances** — the cheapest Azure option for a single container.

### 1. Login

```bash
az login
```

### 2. Create resource group and registry

```bash
az group create --name jokes-mcp-rg --location eastus

az acr create --resource-group jokes-mcp-rg \
  --name jokesmcpregistry --sku Basic
```

### 3. Build and push image (amd64 for Azure)

```bash
az acr update --name jokesmcpregistry --admin-enabled true

docker buildx build --platform linux/amd64 \
  -t jokesmcpregistry.azurecr.io/jokes-mcp:latest \
  --push .
```

### 4. Deploy to ACI

```bash
az container create \
  --resource-group jokes-mcp-rg \
  --name jokes-mcp \
  --image jokesmcpregistry.azurecr.io/jokes-mcp:latest \
  --registry-login-server jokesmcpregistry.azurecr.io \
  --registry-username <acr-username> \
  --registry-password <acr-password> \
  --cpu 0.5 --memory 0.5 \
  --ports 8000 \
  --ip-address Public \
  --dns-name-label jokes-mcp-server \
  --os-type Linux
```

Remote MCP URL:

```
http://jokes-mcp-server.eastus.azurecontainer.io:8000/mcp
```

### Cost estimate

| Resource | Cost |
|----------|------|
| ACI (0.5 vCPU, 0.5 GB) | ~$8/month (24/7) |
| ACR Basic | ~$5/month |

Stop the container when not in use:

```bash
az container stop --name jokes-mcp --resource-group jokes-mcp-rg
az container start --name jokes-mcp --resource-group jokes-mcp-rg
```

---

## Claude Code Integration

The servers are registered in `.mcp.json` at the project root for use directly inside Claude Code:

```json
{
  "mcpServers": {
    "datetime": {
      "command": "python",
      "args": ["<path-to>/MCP Demo/app.py"]
    },
    "jokes": {
      "type": "http",
      "url": "http://jokes-mcp-server.eastus.azurecontainer.io:8000/mcp"
    }
  }
}
```

Restart Claude Code after editing `.mcp.json` for changes to take effect.
