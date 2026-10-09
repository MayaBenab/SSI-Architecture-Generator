# Trace: ['FR04', 'FR13', 'FR19', 'FR21', 'FR28', 'FR29'] / ['NFR08', 'NFR13']

Required functions (21): FR01, FR02, FR03, FR04, FR05, FR06, FR07, FR08, FR09, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR19, FR21, FR28, FR29

| # | pattern | realizes | chosen among | required by | supports | components (Phase 2) | deployment |
|---|---|---|---|---|---|---|---|
| 1 | P02_Trusted_Registration_Authority_Registry | FR04 |  | P10 | NFR08 | (no rule) | (no component added) |
| 2 | P03_Trusted_Accreditation_Registry | FR28 |  | P04 P15 | NFR08 | (no rule) | (no component added) |
| 3 | P04_Trusted_Issuer_Registry | FR19 FR28 |  |  | NFR08 | TIR | Trusted issuer registry: trusted issuer registry approximated by a configured list |
| 4 | P05_Trusted_Schemas_Registry | FR14 |  | P02 P03 P12 P15 | NFR08 NFR13 | TSR | Schema registry: schema registry = ledger schema + credential definition; Verifiable data registry: the Indy ledger (von-network), run outside the compose file |
| 5 | P06_Status_Registry | FR21 |  |  | NFR08 | StatusRegistry | Status / revocation registry: status registry = Indy revocation registry + tails server |
| 6 | P07_DID_Registry | FR05 |  | P10 P24 P27 P28 | NFR08 | DIDRegistry | DID registry (DPKI): DID registry = Indy ledger (von-network); every agent joins the ledger network; Verifiable data registry: the Indy ledger (von-network), run outside the compose file |
| 7 | P10_Onboarding_or_DID_Registration | FR04 | P10/P11 | P16 | NFR08 | (no rule) | (no component added) |
| 8 | P15_Verifiable_Accreditation | FR28 |  |  | NFR08 | (no rule) | (no component added) |
| 9 | P16_Verifiable_Authorization | FR29 |  |  |  | (no rule) | (no component added) |
| 10 | P32_Master_and_Sub_Key | FR01 |  |  |  | KeyMgr_H, MasterKeyStore_H, SubKeyDeriv_H | Key manager (hierarchical): hierarchical keys: Askar wallet (KMS) with per-DID keys; Master key store (offline): approximated: the master key stays in the Askar wallet, not offline; Sub-key derivation: one key per DID, created by the Askar KMS |
| 11 | P24_Public_DIDs | FR02 FR03 FR06 |  | P12 | NFR08 | DIDMgr_I, DIDMgr_V, KeyMgr_I, KeyMgr_V, PublicDID_I, PublicDID_V | DID manager: DID management of the agent (/wallet/did); Key manager: key management of the agent: Askar wallet (KMS); Public DID (did:web/ion) + service endpoint: the issuer's public DID, written to the ledger; Public DID + service endpoint: the verifier's public DID, written to the ledger |
| 12 | P12_Verifiable_ID | FR12 | P12/P13/P14 | P17 | NFR08 | IssuanceSvc, VIDIssuer, CredStore_H | Credential issuance: issue-credential v2 module of the agent; Verifiable ID issuance: Verifiable ID = credential issued over issue-credential v2; Credential store: credentials kept in the wallet (/credentials) |
| 13 | P26_Static_DIDs |  | P25/P26 |  |  | DIDMgr_H, StaticDID_H | DID manager: DID management of the agent (/wallet/did); Static DID (did:key): static did:key, not registered |
| 14 | P27_Dual_Resolution | FR07 FR08 |  | P17 P28 | NFR08 | Resolver_H, Resolver_I, Resolver_V | DID resolver: resolver built into the agent (did:key, did:peer, did:web; did:sov via the ledger) |
| 15 | P40_Identity_Hub |  | P38/P39/P40 |  |  | IdentityHub | Identity hub (external agent): not realised by the Aries stack; Wallet (hub-backed): not realised by the Aries stack |
| 16 | P17_Selective_Content_Generation | FR16 |  |  |  | PresGen_H, VerifSvc, PresVerif_V | Presentation generator (selective disclosure): selective disclosure = present-proof v2 with requested attributes; Presentation verification: present-proof v2 module of the verifier; Presentation verifier: verifies the presentation (verified: true) |
| 17 | P28_On_Chain_Resolution |  | P28/P29 |  | NFR08 |  | (no component added) |
