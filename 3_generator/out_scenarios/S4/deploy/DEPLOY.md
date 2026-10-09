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

## How each component and connector of the architecture is realised
- Holder [holder] (G0): the holder's ACA-Py agent (role typed Holder in G0)
- Issuer [issuer] (G0): the issuer's ACA-Py agent (role typed Issuer in G0)
- Verifier [verifier] (G0): the verifier's ACA-Py agent (role typed Verifier in G0)
- Wallet [issuer] (G0): the agent's Askar wallet: it creates and keeps the agent's DIDs, keys (KMS) and credentials
- Wallet [verifier] (G0): the agent's Askar wallet: it creates and keeps the agent's DIDs, keys (KMS) and credentials
- Verifiable data registry [vdr] <- P07: the Indy ledger (von-network), run outside the compose file
- Trusted issuer registry [vdr] <- P04: trusted issuer registry approximated by a configured list
- Schema registry [vdr] <- P05: schema registry = ledger schema + credential definition
- Status / revocation registry [vdr] <- P06: status registry = Indy revocation registry + tails server
- DID registry (DPKI) [vdr] <- P07: DID registry = Indy ledger (von-network); every agent joins the ledger network
- Key manager (hierarchical) [holder] <- P32: hierarchical keys: Askar wallet (KMS) with per-DID keys
- Master key store (offline) [holder] <- P32: approximated: the master key stays in the Askar wallet, not offline
- Sub-key derivation [holder] <- P32: one key per DID, created by the Askar KMS
- DID manager [issuer] <- P24: DID management of the agent (/wallet/did)
- DID manager [verifier] <- P24: DID management of the agent (/wallet/did)
- Key manager [issuer] <- P24: key management of the agent: Askar wallet (KMS)
- Key manager [verifier] <- P24: key management of the agent: Askar wallet (KMS)
- Public DID (did:web/ion) + service endpoint [issuer] <- P24: the issuer's public DID, written to the ledger
- Public DID + service endpoint [verifier] <- P24: the verifier's public DID, written to the ledger
- Credential issuance [issuer] <- P12: issue-credential v2 module of the agent
- Verifiable ID issuance [issuer] <- P12: Verifiable ID = credential issued over issue-credential v2
- Credential store [holder] <- P12: credentials kept in the wallet (/credentials)
- DID manager [holder] <- P26: DID management of the agent (/wallet/did)
- Static DID (did:key) [holder] <- P26: static did:key, not registered
- DID resolver [holder] <- P27: resolver built into the agent (did:key, did:peer, did:web; did:sov via the ledger)
- DID resolver [issuer] <- P27: resolver built into the agent (did:key, did:peer, did:web; did:sov via the ledger)
- DID resolver [verifier] <- P27: resolver built into the agent (did:key, did:peer, did:web; did:sov via the ledger)
- Presentation generator (selective disclosure) [holder] <- P17: selective disclosure = present-proof v2 with requested attributes
- Presentation verification [verifier] <- P17: present-proof v2 module of the verifier
- Presentation verifier [verifier] <- P17: verifies the presentation (verified: true)
- listed as trusted issuer [registry write] issuer -> vdr: write on the Indy ledger (indy profile)
- check issuer trust [registry read] verifier -> vdr: read on the Indy ledger (indy profile)
- publish / read schema [registry read-write] issuer -> vdr: read and write on the Indy ledger (indy profile)
- check schema [registry read] verifier -> vdr: read on the Indy ledger (indy profile)
- publish status [registry write] issuer -> vdr: write on the Indy ledger (indy profile)
- check status [registry read] verifier -> vdr: read on the Indy ledger (indy profile)
- derive [local] holder -> holder: call inside one agent: nothing to deploy
- publish DID document [registry write] issuer -> vdr: write on the Indy ledger (indy profile)
- publish DID document [registry write] verifier -> vdr: write on the Indy ledger (indy profile)
- controls [local] issuer -> issuer: call inside one agent: nothing to deploy
- controls [local] verifier -> verifier: call inside one agent: nothing to deploy
- stores DIDs [local] issuer -> issuer: call inside one agent: nothing to deploy
- stores DIDs [local] verifier -> verifier: call inside one agent: nothing to deploy
- issue V-ID [issue-credential (DIDComm)] issuer -> holder: Issue Credential v2 between issuer and holder agents
- sign [local] issuer -> issuer: call inside one agent: nothing to deploy
- read schema [registry read] issuer -> vdr: read on the Indy ledger (indy profile)
- controls [local] holder -> holder: call inside one agent: nothing to deploy
- connection [DIDComm] holder -> issuer: DIDComm channel between two agents: DID Exchange 1.1 with did:peer
- connection [DIDComm] holder -> verifier: DIDComm channel between two agents: DID Exchange 1.1 with did:peer
- stores DIDs [local] holder -> holder: call inside one agent: nothing to deploy
- resolve + authenticate [resolution] holder -> issuer: resolver call inside the agent
- resolve + authenticate [resolution] holder -> verifier: resolver call inside the agent
- select claims [local] holder -> holder: call inside one agent: nothing to deploy
- present proof [present-proof (DIDComm)] holder -> verifier: Present Proof v2 between holder and verifier agents
- get issuer key [local] verifier -> verifier: call inside one agent: nothing to deploy
- on-chain resolution [registry read] holder -> vdr: read on the Indy ledger (indy profile)
- on-chain resolution [registry read] verifier -> vdr: read on the Indy ledger (indy profile)
- on-chain resolution [registry read] issuer -> vdr: read on the Indy ledger (indy profile)

## Substitutions in this profile
- Verifiable data registry [vdr] <- P07: no registry in the no-ledger profile
- Schema registry [vdr] <- P05: schema registry replaced by a JSON-LD context (no ledger); the schema is the credential's @context
- Status / revocation registry [vdr] <- P06: revocation registry not exercised (needs the ledger); W3C Status List would be the no-ledger equivalent
- DID registry (DPKI) [vdr] <- P07: not exercised in the no-ledger profile (the ledger is the DID registry)
- Public DID (did:web/ion) + service endpoint [issuer] <- P24: public DIDs replaced by did:key for issuer and verifier (no registry)
- listed as trusted issuer [registry write] issuer -> vdr: not exercised without a ledger
- check issuer trust [registry read] verifier -> vdr: not exercised without a ledger
- publish / read schema [registry read-write] issuer -> vdr: not exercised without a ledger
- check schema [registry read] verifier -> vdr: not exercised without a ledger
- publish status [registry write] issuer -> vdr: not exercised without a ledger
- check status [registry read] verifier -> vdr: not exercised without a ledger
- publish DID document [registry write] issuer -> vdr: not exercised without a ledger
- publish DID document [registry write] verifier -> vdr: not exercised without a ledger
- read schema [registry read] issuer -> vdr: not exercised without a ledger
- on-chain resolution [registry read] holder -> vdr: not exercised without a ledger
- on-chain resolution [registry read] verifier -> vdr: not exercised without a ledger
- on-chain resolution [registry read] issuer -> vdr: not exercised without a ledger

## Elements the stack does not realise (reported, not silently dropped)
- Wallet (hub-backed) [holder] <- P40: not realised by the Aries stack
- Identity hub (external agent) [identityhub] <- P40: not realised by the Aries stack
- replicate [hub protocol] holder -> identityhub: not realised by the Aries stack
