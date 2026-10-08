# Trace: ['FR13', 'FR17'] / ['NFR09', 'NFR11']

Required functions (15): FR01, FR02, FR03, FR06, FR07, FR08, FR09, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17

| # | pattern | realizes | chosen among | required by | supports | components (Phase 2) | deployment |
|---|---|---|---|---|---|---|---|
| 1 | P32_Master_and_Sub_Key | FR01 |  | P26 |  | KeyMgr_H, MasterKeyStore_H, SubKeyDeriv_H | hierarchical keys: Askar wallet (KMS) with per-DID keys |
| 2 | P07_DID_Registry |  |  | P24 P27 P28 | NFR09 | DIDRegistry | DID registry = Indy ledger (von-network) |
| 3 | P24_Public_DIDs | FR02 FR03 FR06 |  | P12 | NFR09 | DIDMgr_I, DIDMgr_V, KeyMgr_I, KeyMgr_V, PublicDID_I, PublicDID_V | public DIDs written to the ledger |
| 4 | P26_Static_DIDs |  | P25/P26 |  |  | DIDMgr_H, StaticDID_H | static did:key, not registered |
| 5 | P27_Dual_Resolution | FR07 FR08 |  | P17 P28 |  | Resolver_H, Resolver_I, Resolver_V | DID resolution built into every agent (did:key, did:peer, did:web; did:sov via the ledger) |
| 6 | P28_On_Chain |  | P28/P29 |  |  |  | on-chain resolution: resolver reads the ledger (indy profile) |
| 7 | P05_Trusted_Schemas_Registry | FR14 |  | P12 |  | TSR | schema registry = ledger schema + cred def |
| 8 | P12_Verifiable_ID | FR12 | P12/P13/P14 | P17 |  | IssuanceSvc, VIDIssuer, Wallet, CredStore_H | Verifiable ID = credential issued over issue-credential v2 |
| 9 | P39_External |  | P38/P39/P40 |  | NFR09 NFR11 | CloudStore | cloud-backed wallet = Postgres storage |
| 10 | P17_Selective_Content_Generation | FR16 |  |  |  | PresGen_H, VerifSvc, PresVerif_V | selective disclosure = present-proof v2 with requested attributes |
