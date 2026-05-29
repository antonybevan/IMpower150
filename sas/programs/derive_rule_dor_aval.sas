/* =====================================================================
   GENERATED PROGRAM FOR DERIVATION RULE: RULE_DOR_AVAL
   TARGET VARIABLE: AVAL
   CLINICAL ENDPOINT: EP_SEC_DOR_9 (DOR)
   ESTIMAND: EST_OS_WT
   RECIST CRITERIA: RECIST_1.1 | ASSESSOR: INVESTIGATOR
   ===================================================================== */

%include "C:\Users\91936\OneDrive\Desktop\IMpower150\sas\templates\derive_date_diff.sas";

%derive_date_diff(outds=work.out_dor, inds=work.raw_data, targetvar=AVAL, startvar=RSPDT, endvar=min(PDDT, DTHDT));
