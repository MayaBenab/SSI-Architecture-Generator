# Trace: ['FR06', 'FR08'] / ['NFR02', 'NFR18']

Required functions (6): FR01, FR02, FR03, FR06, FR07, FR08

| # | pattern | realizes | chosen among | required by | supports | components (Phase 2) | deployment |
|---|---|---|---|---|---|---|---|
| 1 | P07_DID_Registry |  |  | P24 P27 |  | DIDRegistry | DID registry (DPKI): DID registry = Indy ledger (von-network); every agent joins the ledger network; Verifiable data registry: the Indy ledger (von-network), run outside the compose file |
| 2 | P32_Master_and_Sub_Key | FR01 |  |  |  | KeyMgr_H, MasterKeyStore_H, SubKeyDeriv_H | Key manager (hierarchical): hierarchical keys: Askar wallet (KMS) with per-DID keys; Master key store (offline): approximated: the master key stays in the Askar wallet, not offline; Sub-key derivation: one key per DID, created by the Askar KMS |
| 3 | P24_Public_DIDs | FR02 FR03 FR06 |  |  |  | DIDMgr_I, DIDMgr_V, KeyMgr_I, KeyMgr_V, PublicDID_I, PublicDID_V | DID manager: DID management of the agent (/wallet/did); Key manager: key management of the agent: Askar wallet (KMS); Public DID (did:web/ion) + service endpoint: the issuer's public DID, written to the ledger; Public DID + service endpoint: the verifier's public DID, written to the ledger |
| 4 | P25_Pairwise_DIDs |  | P25/P26 | P29 | NFR02 NFR18 | DIDMgr_H, PairwiseDID_H | DID manager: DID management of the agent (/wallet/did); Pairwise DID manager (did:peer): a did:peer per connection (DID Exchange, default in ACA-Py 1.x) |
| 5 | P27_Dual_Resolution | FR07 FR08 |  | P29 | NFR02 | Resolver_H, Resolver_I, Resolver_V | DID resolver: resolver built into the agent (did:key, did:peer, did:web; did:sov via the ledger) |
| 6 | P29_Off_Chain_Resolution |  | P28/P29 |  | NFR18 |  | (no component added) |

Trade-offs: nfr18: strongly hindered by P24 Public DIDs, forced by the requested functions
