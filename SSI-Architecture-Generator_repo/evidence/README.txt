Evidence of the execution of scenario S1 on the Indy profile (2026-10-05)

S1_indy_presentation_record.json   export of GET http://localhost:8041/present-proof-2.0/records on the verifier agent
  - pres_ex_id db97da83-..., role verifier, state done, verified true (16:52:43Z)
  - request: requested_attributes = {degree}, restricted to cred_def_id 4fUDR9R7fjwELRvH9JT6HH:3:CL:10:default
  - presentation: revealed_attrs = {degree: "Master of Computer Science"}; college and year NOT revealed
  - identifiers: schema 4fUDR9R7fjwELRvH9JT6HH:2:diploma:1.0, cred def 4fUDR9R7fjwELRvH9JT6HH:3:CL:10:default (both on the ledger)
S1_indy_Deployment.png             deployment diagram of that run (indy profile)

Other observations of the run (not exported): issuer public DID 4fUDR9R7fjwELRvH9JT6HH (did:sov, posted), schema = ledger transaction 10.
