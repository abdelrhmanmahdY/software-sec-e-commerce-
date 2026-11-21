#!/usr/bin/env bash
# Generates a SELF-SIGNED certificate for local/dev HTTPS (browsers will warn).
# For production use a CA certificate - see docs/TLS_AAA.md (Let's Encrypt).
set -euo pipefail

CERT_DIR="${1:-certs}"
DOMAIN="${DOMAIN:-localhost}"
mkdir -p "$CERT_DIR"

if [[ -f "$CERT_DIR/fullchain.pem" && -f "$CERT_DIR/privkey.pem" ]]; then
  echo "Certificates already exist in $CERT_DIR (delete them to regenerate)."
  exit 0
fi

openssl req -x509 -newkey rsa:2048 -sha256 -nodes -days 365 \
  -keyout "$CERT_DIR/privkey.pem" -out "$CERT_DIR/fullchain.pem" \
  -subj "/CN=${DOMAIN}" \
  -addext "subjectAltName=DNS:${DOMAIN},DNS:localhost,IP:127.0.0.1"
chmod 600 "$CERT_DIR/privkey.pem"
echo "Created $CERT_DIR/fullchain.pem and $CERT_DIR/privkey.pem for ${DOMAIN}"
