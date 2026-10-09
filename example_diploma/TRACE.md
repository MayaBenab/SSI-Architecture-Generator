# Trace: ['FR13', 'FR17'] / ['NFR04', 'NFR07']

Required functions (15): FR01, FR02, FR03, FR06, FR07, FR08, FR09, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17

| # | pattern | realizes | chosen among | required by | supports | components (Phase 2) | deployment |
|---|---|---|---|---|---|---|---|
| 1 | P05_Trusted_Schemas_Registry | FR14 |  | P12 |  | TSR | Schema registry: schema registry = ledger schema + credential definition; Verifiable data registry: the Indy ledger (von-network), run outside the compose file |
| 2 | P07_DID_Registry |  |  | P24 P27 |  | DIDRegistry | DID registry (DPKI): DID registry = Indy ledger (von-network); every agent joins the ledger network; Verifiable data registry: the Indy ledger (von-network), run outside the compose file |
| 3 | P32_Master_and_Sub_Key | FR01 |  |  | NFR04 NFR07 | KeyMgr_H, MasterKeyStore_H, SubKeyDeriv_H | Key manager (hierarchical): hierarchical keys: Askar wallet (KMS) with per-DID keys; Master key store (offline): approximated: the master key stays in the Askar wallet, not offline; Sub-key derivation: one key per DID, created by the Askar KMS |
| 4 | P24_Public_DIDs | FR02 FR03 FR06 |  | P12 |  | DIDMgr_I, DIDMgr_V, KeyMgr_I, KeyMgr_V, PublicDID_I, PublicDID_V | DID manager: DID management of the agent (/wallet/did); Key manager: key management of the agent: Askar wallet (KMS); Public DID (did:web/ion) + service endpoint: the issuer's public DID, written to the ledger; Public DID + service endpoint: the verifier's public DID, written to the ledger |
| 5 | P12_Verifiable_ID | FR12 | P12/P13/P14 | P17 |  | IssuanceSvc, VIDIssuer, CredStore_H | Credential issuance: issue-credential v2 module of the agent; Verifiable ID issuance: Verifiable ID = credential issued over issue-credential v2; Credential store: credentials kept in the wallet (/credentials) |
| 6 | P25_Pairwise_DIDs |  | P25/P26 | P29 | NFR04 | DIDMgr_H, PairwiseDID_H | DID manager: DID management of the agent (/wallet/did); Pairwise DID manager (did:peer): a did:peer per connection (DID Exchange, default in ACA-Py 1.x) |
| 7 | P27_Dual_Resolution | FR07 FR08 |  | P17 P29 |  | Resolver_H, Resolver_I, Resolver_V | DID resolver: resolver built into the agent (did:key, did:peer, did:web; did:sov via the ledger) |
| 8 | P38_Local_Storage |  | P38/P39/P40 |  | NFR04 NFR07 | LocalStore_H | Local encrypted store: local encrypted SQLite wallet; Wallet (local): local Askar wallet: the holder's DIDs, keys (KMS) and credentials, in a local encrypted store |
| 9 | P17_Selective_Content_Generation | FR16 |  |  | NFR04 | PresGen_H, VerifSvc, PresVerif_V | Presentation generator (selective disclosure): selective disclosure = present-proof v2 with requested attributes; Presentation verification: present-proof v2 module of the verifier; Presentation verifier: verifies the presentation (verified: true) |
| 10 | P29_Off_Chain_Resolution |  | P28/P29 |  | NFR04 |  | (no component added) |
