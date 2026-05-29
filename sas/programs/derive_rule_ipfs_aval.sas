/* =====================================================================
   GENERATED PROGRAM FOR DERIVATION RULE: RULE_IPFS_AVAL
   TARGET VARIABLE: AVAL
   CLINICAL ENDPOINT: EP_IPFS_ITT (iPFS)
   ESTIMAND: EST_IPFS_ITT
   RECIST CRITERIA: iRECIST | ASSESSOR: INVESTIGATOR
   ===================================================================== */

%include "C:\Users\91936\OneDrive\Desktop\IMpower150\sas\templates\derive_iupd_flag.sas";

%derive_iupd_flag(outds=work.out_iupd, inds=work.raw_data, targetvar=IUPD_FL, iupd_dt=IUPD_DT, confirmation_dt=CONF_DT, confirmation_window=28);
