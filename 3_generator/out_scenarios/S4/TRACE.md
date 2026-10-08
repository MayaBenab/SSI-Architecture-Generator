# Trace: ['FR04', 'FR13', 'FR19', 'FR21', 'FR28', 'FR29'] / ['NFR08', 'NFR13']

Required functions (21): FR01, FR02, FR03, FR04, FR05, FR06, FR07, FR08, FR09, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR19, FR21, FR28, FR29

| # | pattern | realizes | chosen among | required by | supports | components (Phase 2) | deployment |
|---|---|---|---|---|---|---|---|
| 1 | P32_Master_and_Sub_Key | FR01 |  | P26 |  | KeyMgr_H, MasterKeyStore_H, SubKeyDeriv_H | hierarchical keys: Askar wallet (KMS) with per-DID keys |
| 2 | P07_DID_Registry | FR05 |  | P10 P24 P27 P28 | NFR08 | DIDRegistry | DID registry = Indy ledger (von-network) |
| 3 | P24_Public_DIDs | FR02 FR03 FR06 |  | P12 | NFR08 | DIDMgr_I, DIDMgr_V, KeyMgr_I, KeyMgr_V, PublicDID_I, PublicDID_V | public DIDs written to the ledger |
| 4 | P26_Static_DIDs |  | P25/P26 |  |  | DIDMgr_H, StaticDID_H | static did:key, not registered |
| 5 | P05_Trusted_Schemas_Registry | FR14 |  | P02 P03 P12 P15 | NFR08 NFR13 | TSR | schema registry = ledger schema + cred def |
| 6 | P02_Trusted_Registration_Authority_Registry | FR04 |  | P10 | NFR08 | (no rule) | NOT REALISED |
| 7 | P10_Onboarding_or_DID_Registration | FR04 | P10/P11 | P16 | NFR08 | (no rule) | NOT REALISED |
| 8 | P27_Dual_Resolution | FR07 FR08 |  | P17 P28 | NFR08 | Resolver_H, Resolver_I, Resolver_V | DID resolution built into every agent (did:key, did:peer, did:web; did:sov via the ledger) |
| 9 | P28_On_Chain |  | P28/P29 |  | NFR08 |  | on-chain resolution: resolver reads the ledger (indy profile) |
| 10 | P12_Verifiable_ID | FR12 | P12/P13/P14 | P17 | NFR08 | IssuanceSvc, VIDIssuer, Wallet, CredStore_H | Verifiable ID = credential issued over issue-credential v2 |
| 11 | P40_Identity_Hub |  | P38/P39/P40 |  |  | IdentityHub | NOT REALISED |
| 12 | P17_Selective_Content_Generation | FR16 |  |  |  | PresGen_H, VerifSvc, PresVerif_V | selective disclosure = present-proof v2 with requested attributes |
| 13 | P03_Trusted_Accreditation_Registry | FR28 |  | P04 P15 | NFR08 | (no rule) | NOT REALISED |
| 14 | P04_Trusted_Issuer_Registry | FR19 FR28 |  |  | NFR08 | TIR | trusted issuer registry approximated by a configured list |
| 15 | P06_Status_Registry | FR21 |  |  | NFR08 | StatusRegistry | status registry = Indy revocation registry + tails server |
| 16 | P15_Verifiable_Accreditation | FR28 |  |  | NFR08 | (no rule) | NOT REALISED |
| 17 | P16_Verifiable_Authorization | FR29 |  |  |  | (no rule) | NOT REALISED |
