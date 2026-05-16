FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir fastmcp uvicorn starlette

COPY jokes_mcp.py .

EXPOSE 8000

CMD ["python", "jokes_mcp.py"]
