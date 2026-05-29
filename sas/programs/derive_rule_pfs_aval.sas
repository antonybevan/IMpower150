/* =====================================================================
   GENERATED PROGRAM FOR DERIVATION RULE: RULE_PFS_AVAL
   TARGET VARIABLE: AVAL
   CLINICAL ENDPOINT: EP_PFS_WT (PFS)
   ESTIMAND: EST_PFS_WT
   RECIST CRITERIA: RECIST_1.1 | ASSESSOR: INVESTIGATOR
   ===================================================================== */

%include "C:\Users\91936\OneDrive\Desktop\IMpower150\sas\templates\derive_date_diff.sas";

%derive_date_diff(outds=work.out_pfs, inds=work.raw_data, targetvar=AVAL, startvar=RANDDT, endvar=PFSDT);
