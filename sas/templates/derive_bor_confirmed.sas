%macro derive_bor_confirmed(outds=, inds=, targetvar=, raw_resp=, conf_resp=, window=28);
data &outds;
    set &inds;
    if &raw_resp in ('CR', 'PR') and not missing(&conf_resp) then &targetvar = 'Y';
    else &targetvar = 'N';
run;
%mend derive_bor_confirmed;
