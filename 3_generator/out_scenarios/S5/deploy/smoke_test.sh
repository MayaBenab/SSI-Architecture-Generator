#!/usr/bin/env bash
# smoke test (no-ledger profile): exercises the requested functions on the deployed agents through the ACA-Py admin API
set -e
H=http://localhost:8021; I=http://localhost:8031; V=http://localhost:8041
echo '1. agents up'; for a in $H $I $V; do curl -sf $a/status/ready >/dev/null && echo "   $a ready"; done
echo '2. connection holder <-> issuer (DID Exchange, did:peer)'
INV=$(curl -s -X POST "$I/out-of-band/create-invitation?auto_accept=true" -H 'Content-Type: application/json' -d '{"handshake_protocols":["https://didcomm.org/didexchange/1.1"]}' | python3 -c 'import sys,json; print(json.dumps(json.load(sys.stdin)["invitation"]))')
curl -s -X POST "$H/out-of-band/receive-invitation?auto_accept=true" -H 'Content-Type: application/json' -d "$INV" >/dev/null; sleep 3
curl -s $H/connections | python3 -c 'import sys,json; c=json.load(sys.stdin)["results"]; print("   connections:", [x["state"] for x in c])'
echo 'done'
