/* =====================================================================
   GENERATED PROGRAM FOR DERIVATION RULE: RULE_OS_CNSR
   TARGET VARIABLE: CNSR
   CLINICAL ENDPOINT: EP_PRM_OS_2 (OS)
   ESTIMAND: EST_OS_WT
   RECIST CRITERIA: RECIST_1.1 | ASSESSOR: INVESTIGATOR
   ===================================================================== */

%include "C:\Users\91936\OneDrive\Desktop\IMpower150\sas\templates\derive_event_flag.sas";

%derive_event_flag(outds=work.out_os_cnsr, inds=work.raw_data, targetvar=CNSR, datevar=OSDT, censorvar=LSTALVDT, pdvar=., deathvar=DTHDT);
