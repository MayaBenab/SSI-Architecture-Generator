# Deployment of the generated architecture (Aries stack, no-ledger profile)

Run: `docker compose config` (validity), `docker compose up -d`, then `bash smoke_test.sh` (agents up, one connection).
Indy profile, diploma case: `python 12_play_diploma.py <this folder>` registers the public DIDs, starts the agents and plays issuance and presentation.
Admin APIs with Swagger: holder http://localhost:8021/api/doc, issuer http://localhost:8031/api/doc, verifier http://localhost:8041/api/doc.

Profiles: no-ledger (default, runnable at once) or Indy (`python 10_generate.py ... --indy`), after building the ledger:
`git clone https://github.com/bcgov/von-network && cd von-network && ./manage build && ./manage start` (ledger console on http://localhost:9000).

## Services
- holder: ACA-Py agent (ghcr.io/openwallet-foundation/acapy-agent:py3.12-1.3-lts), ports 8020 / admin 8021
- issuer: ACA-Py agent (ghcr.io/openwallet-foundation/acapy-agent:py3.12-1.3-lts), ports 8030 / admin 8031
- verifier: ACA-Py agent (ghcr.io/openwallet-foundation/acapy-agent:py3.12-1.3-lts), ports 8040 / admin 8041

## What each selected pattern became
- P04: trusted issuer registry approximated by a configured list
- P05: schema registry = ledger schema + cred def
- P06: status registry = Indy revocation registry + tails server
- P07: DID registry = Indy ledger (von-network)
- P12: Verifiable ID = credential issued over issue-credential v2
- P17: selective disclosure = present-proof v2 with requested attributes
- P24: public DIDs written to the ledger
- P26: static did:key, not registered
- P27: DID resolution built into every agent (did:key, did:peer, did:web; did:sov via the ledger)
- P28: on-chain resolution: resolver reads the ledger (indy profile)
- P32: hierarchical keys: Askar wallet (KMS) with per-DID keys

## Substitutions in this profile
- P05: schema registry replaced by a JSON-LD context (no ledger); the schema is the credential's @context
- P06: revocation registry not exercised (needs the ledger); W3C Status List would be the no-ledger equivalent
- P07: not exercised in the no-ledger profile (the ledger is the DID registry)
- P24: public DIDs replaced by did:key for issuer and verifier (no registry)

## Patterns the stack does not realise (reported, not silently dropped)
- P02 (no mapping yet)
- P03 (no mapping yet)
- P10 (no mapping yet)
- P15 (no mapping yet)
- P16 (no mapping yet)
- P40
