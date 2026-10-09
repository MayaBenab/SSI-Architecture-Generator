"""Step 5 (test) for the diploma case, Indy profile: plays the requested functions on the generated deployment through the
ACA-Py admin APIs, as in the run of 5 Oct 2026 (evidence/). Standard library only.

Before: the von-network ledger is running (http://localhost:9000) and the deployment was generated with --indy:
    python 10_generate.py FR13 FR17 --nfr NFR04 NFR07 --out out_diploma --indy
usage: python 12_play_diploma.py [out_diploma/deploy]   (no argument: the deployment written by 10_generate.py without arguments)

What it does (each line of output is one function of the request, or one of the 13 added by depends):
  1. registers the issuer's and verifier's public DIDs on the ledger from their seeds (P24, P07), then starts the agents
  2. issuer: diploma schema and credential definition on the ledger (P05)
  3. holder <-> issuer, holder <-> verifier: DID Exchange, one pairwise did:peer per relation (P25, P29, P27)
  4. issuer -> holder: the diploma VC (P12), stored in the holder's local wallet (P38)
  5. verifier asks for 'degree' only; holder presents it alone (P17); verifier verifies against the ledger -> verified: true
"""
import json, os, re, subprocess, sys, time, urllib.request

H, I, V = "http://localhost:8021", "http://localhost:8031", "http://localhost:8041"
LEDGER = "http://localhost:9000"


def call(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        txt = r.read().decode()
        return json.loads(txt) if txt else {}


def wait(what, fn, timeout=90):
    t = time.time()
    while time.time() - t < timeout:
        try:
            x = fn()
            if x: return x
        except Exception:
            pass
        time.sleep(2)
    sys.exit(f"   FAILED: {what} (timeout {timeout}s)")


def seed_of(deploy_dir, role):
    args = open(os.path.join(deploy_dir, f"{role}.args"), encoding="utf-8").read()
    m = re.search(r"--seed (\S+)", args)
    if not m: sys.exit(f"no --seed in {role}.args: generate the deployment with --indy")
    return m.group(1)


def connect(inviter, invitee):
    inv = call("POST", f"{inviter}/out-of-band/create-invitation?auto_accept=true",
               {"handshake_protocols": ["https://didcomm.org/didexchange/1.1"]})["invitation"]
    rec = call("POST", f"{invitee}/out-of-band/receive-invitation?auto_accept=true", inv)
    cid_invitee = rec.get("connection_id")
    wait("connection active", lambda: call("GET", f"{invitee}/connections/{cid_invitee}")["state"] in ("active", "completed"))
    cid_inviter = wait("inviter side", lambda: next((c["connection_id"] for c in call("GET", f"{inviter}/connections")["results"]
                                                     if c.get("invitation_msg_id") == inv["@id"] and c["state"] in ("active", "completed")), None))
    my_did = call("GET", f"{invitee}/connections/{cid_invitee}").get("my_did")
    return cid_inviter, cid_invitee, my_did


def main():
    deploy_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_diploma", "deploy")
    print("1. public DIDs of issuer and verifier on the ledger (P24, P07)")
    for role in ("issuer", "verifier"):
        r = call("POST", f"{LEDGER}/register", {"seed": seed_of(deploy_dir, role), "role": "ENDORSER", "alias": role})
        print(f"   {role}: {r.get('did')} registered")
    subprocess.run(["docker", "compose", "up", "-d"], cwd=deploy_dir, check=True)
    for a in (H, I, V): wait(f"agent {a} ready", lambda a=a: call("GET", f"{a}/status/ready").get("ready"))
    for a, role in ((I, "issuer"), (V, "verifier")):
        print(f"   {role} public DID: {call('GET', f'{a}/wallet/did/public')['result']['did']}")

    print("2. diploma schema and credential definition on the ledger (P05)")
    s = call("POST", f"{I}/schemas", {"schema_name": "diploma", "schema_version": "1.0", "attributes": ["name", "degree", "college", "year"]})
    schema_id = s.get("schema_id") or s["sent"]["schema_id"]
    c = call("POST", f"{I}/credential-definitions", {"schema_id": schema_id, "tag": "default", "support_revocation": False})
    cred_def_id = c.get("credential_definition_id") or c["sent"]["credential_definition_id"]
    print(f"   schema {schema_id}\n   cred def {cred_def_id}")

    print("3. connections by DID Exchange, one pairwise did:peer per relation (P25, P29, P27)")
    ci_h, _, did_hi = connect(I, H)
    cv_h, _, did_hv = connect(V, H)
    print(f"   holder's DID with the issuer:   {did_hi}\n   holder's DID with the verifier: {did_hv}  (distinct: {did_hi != did_hv})")

    print("4. issuance of the diploma VC; stored in the holder's local wallet (P12, P38)")
    call("POST", f"{I}/issue-credential-2.0/send", {
        "connection_id": ci_h, "filter": {"indy": {"cred_def_id": cred_def_id}},
        "credential_preview": {"@type": "issue-credential/2.0/credential-preview", "attributes": [
            {"name": "name", "value": "Alice"}, {"name": "degree", "value": "Master of Computer Science"},
            {"name": "college", "value": "Faculty of Science"}, {"name": "year", "value": "2026"}]}})
    cred = wait("credential stored", lambda: next(iter(call("GET", f"{H}/credentials")["results"]), None))
    print(f"   stored credential {cred['referent']} with attributes {sorted(cred['attrs'])}")

    print("5. presentation of 'degree' only (P17), verified against the ledger")
    call("POST", f"{V}/present-proof-2.0/send-request", {"connection_id": cv_h, "presentation_request": {"indy": {
        "name": "diploma-check", "version": "1.0", "nonce": "1234567890", "requested_predicates": {},
        "requested_attributes": {"degree": {"name": "degree", "restrictions": [{"cred_def_id": cred_def_id}]}}}}})
    rec = wait("request received by the holder", lambda: next(iter(call("GET", f"{H}/present-proof-2.0/records?state=request-received")["results"]), None))
    pid = rec["pres_ex_id"]
    ref = call("GET", f"{H}/present-proof-2.0/records/{pid}/credentials")[0]["cred_info"]["referent"]
    call("POST", f"{H}/present-proof-2.0/records/{pid}/send-presentation", {"indy": {
        "requested_attributes": {"degree": {"cred_id": ref, "revealed": True}}, "requested_predicates": {}, "self_attested_attributes": {}}})

    def verifier_record():
        r = next(iter(call("GET", f"{V}/present-proof-2.0/records")["results"]), None)
        if r and r["state"] == "presentation-received":
            call("POST", f"{V}/present-proof-2.0/records/{r['pres_ex_id']}/verify-presentation"); return None
        return r if r and r["state"] == "done" else None
    done = wait("presentation verified", verifier_record)
    out = os.path.join(deploy_dir, "presentation_record.json")
    json.dump(done, open(out, "w", encoding="utf-8"), indent=1)
    print(f"   verifier record: state {done['state']}, verified: {done.get('verified')}  (exported to {out})")


if __name__ == "__main__":
    main()
