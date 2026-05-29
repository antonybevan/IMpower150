/* =====================================================================
   GENERATED PROGRAM FOR DERIVATION RULE: RULE_ORR_FL
   TARGET VARIABLE: ORR_FL
   CLINICAL ENDPOINT: EP_SEC_BOR_1 (BOR)
   ESTIMAND: EST_OS_WT
   RECIST CRITERIA: RECIST_1.1 | ASSESSOR: INVESTIGATOR
   ===================================================================== */

%include "C:\Users\91936\OneDrive\Desktop\IMpower150\sas\templates\derive_conditional.sas";

%derive_conditional(outds=work.out_orr, inds=work.raw_data, targetvar=ORR_FL, condvar=rsorres, condvals='CR', 'PR', trueval='Y', falseval='N');
