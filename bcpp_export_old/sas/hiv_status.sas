

# documented HIV positive 
if recorded_hiv_result="POS" or (other_record="Yes" and result_recorded ne "NEG")
       then my_docd_pos=1;
     else if recorded_hiv_result not in ("POS" "NEG") and
       not (other_record="YES" and result_recorded="POS")
       then my_docd_pos=.;
     else my_docd_pos=0;

     
# today's test and a documented positive
 hiv_pos = .;
 if today_hiv_result = 'POS' then hiv_pos = 1;
 if today_hiv_result = 'NEG' then hiv_pos = 0;
 if today_hiv_result not in ("POS" "NEG") and my_docd_pos = 1 then hiv_pos = 1;

1, 0 , .

# art status
# (naive 1, defaulter 2, on art 3)

if hiv_pos ne 1 then art_3cat=.;
 else if ever_taken_arv='No' or (hiv_pos=1 and ever_taken_arv = ' ')
        then art_3cat = 1;
     else if hiv_pos=1 and ever_taken_arv= 'Yes' and on_arv = 'No' then art_3cat=2;
     else if hiv_pos=1 and on_arv="Yes" then art_3cat=3;
     
# new_pos
today_hiv_result = 'POS'

# defaulter
else if hiv_pos=1 and ever_taken_arv= 'Yes' and on_arv = 'No' then art_3cat=2;

# aware of status
(kathleen)
f recorded_hiv_result in ("POS" "NEG") or result_recorded in ("POS" "NEG") or art_3cat in (2 3)
   then prev_result_known = 1;
 else prev_result_known = 0;

 if prev_result_known then do;
      if recorded_hiv_result = "POS" or result_recorded = "POS" or art_3cat in (2 3)
     then prev_result = "POS";
   else prev_result = "NEG";
 end;
 else prev_result=" ";

 # tested in the last 12 months (HTC coverage)
 myprior_test_date = hiv_test_date;
 myintv_date = visit_date;
    format myprior_test_date myintv_date date9.;

 if prev_result = "NEG" and (myprior_test_date ne . and (myintv_date - myprior_test_date) <= 365.25)
  then my_docd_neg_12mo = 1;

 if prev_result = "POS" or my_docd_neg_12mo = 1 then my_htc_coverage_12mo = 1;
 else if prev_result ne "" or my_docd_neg_12mo ne . then my_htc_coverage_12mo = 0;
 else my_htc_coverage_12mo = .;

