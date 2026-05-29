/* =====================================================================
   GENERATED PROGRAM FOR DERIVATION RULE: RULE_PFS_CNSR
   TARGET VARIABLE: CNSR
   CLINICAL ENDPOINT: EP_PFS_WT (PFS)
   ESTIMAND: EST_PFS_WT
   RECIST CRITERIA: RECIST_1.1 | ASSESSOR: INVESTIGATOR
   ===================================================================== */

%include "C:\Users\91936\OneDrive\Desktop\IMpower150\sas\templates\derive_event_flag.sas";

%derive_event_flag(outds=work.out_pfs_cnsr, inds=work.raw_data, targetvar=CNSR, datevar=PFSDT, censorvar=LSTALVDT, pdvar=PDDT, deathvar=DTHDT);
