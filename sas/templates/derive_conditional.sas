%macro derive_conditional(outds=, inds=, targetvar=, condvar=, condvals=, trueval=, falseval=);
data &outds;
    set &inds;
    if &condvar in (&condvals) then &targetvar = &trueval;
    else &targetvar = &falseval;
run;
%mend derive_conditional;
