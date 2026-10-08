#!/usr/bin/env bash
# smoke test (indy profile): exercises the requested functions on the deployed agents through the ACA-Py admin API
set -e
H=http://localhost:8021; I=http://localhost:8031; V=http://localhost:8041
echo '1. agents up'; for a in $H $I $V; do curl -sf $a/status/ready >/dev/null && echo "   $a ready"; done
echo '2. connection holder <-> issuer (DID Exchange, did:peer)'
INV=$(curl -s -X POST "$I/out-of-band/create-invitation?auto_accept=true" -H 'Content-Type: application/json' -d '{"handshake_protocols":["https://didcomm.org/didexchange/1.1"]}' | python3 -c 'import sys,json; print(json.dumps(json.load(sys.stdin)["invitation"]))')
curl -s -X POST "$H/out-of-band/receive-invitation?auto_accept=true" -H 'Content-Type: application/json' -d "$INV" >/dev/null; sleep 3
curl -s $H/connections | python3 -c 'import sys,json; c=json.load(sys.stdin)["results"]; print("   connections:", [x["state"] for x in c])'
echo '3. issuer: POST /schemas {schema_name, schema_version, attributes} -> schema_id on the ledger'   # admin API call to complete for the scenario
echo '4. issuer: POST /credential-definitions {schema_id, tag, support_revocation:false} -> cred_def_id'   # admin API call to complete for the scenario
echo '5. issuer -> holder: POST /issue-credential-2.0/send with filter.ld_proof (JSON-LD, did:key) in the no-ledger profile, or filter.indy {cred_def_id} + credential_preview in the indy profile; holder: GET /credentials'   # admin API call to complete for the scenario
echo '6. verifier: POST /present-proof-2.0/send-request - dif {options{challenge,domain}, presentation_definition{id:uuid,...}} in no-ledger, or indy {requested_attributes restricted to the cred_def_id} in indy; holder: POST /records/{id}/send-presentation (dif: issuer_id = holder did:key, record_ids; indy: cred_id, revealed); verifier: state done, verified true'   # admin API call to complete for the scenario
echo '7. register the issuer and verifier public DIDs on the ledger (von-network :9000, Register from seed, role Endorser) BEFORE starting the agents; check GET /wallet/did/public -> posture posted'   # admin API call to complete for the scenario
echo 'done'
