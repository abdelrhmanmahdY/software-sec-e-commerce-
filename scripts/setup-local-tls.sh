
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v mkcert >/dev/null 2>&1; then
    echo "ERROR: Install mkcert first."
    exit 1
fi

mkdir -p certs

# Install the local CA into the host trust stores.
mkcert -install

# Generate certificates only if they don't already exist.
if [[ ! -s certs/fullchain.pem || ! -s certs/privkey.pem ]]; then
    mkcert \
      -cert-file certs/fullchain.pem \
      -key-file certs/privkey.pem \
      localhost 127.0.0.1 ::1
else
    echo "Existing TLS certificates found. Reusing them."
fi

chmod 644 certs/fullchain.pem
chmod 600 certs/privkey.pem

echo "TLS setup completed."
