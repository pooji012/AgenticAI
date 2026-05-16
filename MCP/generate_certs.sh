#!/bin/bash
# Generate a self-signed SSL certificate for local HTTPS development

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

openssl req -x509 \
  -newkey rsa:4096 \
  -keyout "$SCRIPT_DIR/key.pem" \
  -out "$SCRIPT_DIR/cert.pem" \
  -days 365 \
  -nodes \
  -subj "/CN=localhost"

echo ""
echo "Certificates generated:"
echo "  cert.pem — SSL certificate"
echo "  key.pem  — Private key"
echo ""
echo "Run the server: python jokes_mcp.py"
