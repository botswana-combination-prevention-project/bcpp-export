***final HIV Status

* HIV status: 1 = infected, 0 = uninfected *;
if recorded_hiv_result="POS" or (other_record="Yes" and result_recorded = 'POS') or (arv_evidence = 'Yes') 
  then my_docd_pos=1;
     else if recorded_hiv_result not in ("POS" "NEG") and
       not (other_record="YES" and result_recorded="POS")
       then my_docd_pos=.;
     else my_docd_pos=0;


    final_hiv_status = .;
    if today_hiv_result = 'POS' then final_hiv_status = 1;
    if today_hiv_result = 'NEG' then final_hiv_status = 0;
    if today_hiv_result not in ("POS" "NEG") and my_docd_pos = 1 then final_hiv_status = 1;

* Final ARV Status -  1: art naive, 2: art defaulters,  3: currently on art ;
    if final_hiv_status ne 1 then final_arv_Status=.;
    if final_hiv_status = 1 and ever_taken_arv='No' or (final_hiv_status=1 and (ever_taken_arv in (' ' 'DWTA'))) then final_arv_status = 1;
    if final_hiv_status=1 and (ever_taken_arv= 'Yes' and on_arv = 'No') or (arv_evidence='Yes' and on_arv = 'No') then Final_ARV_Status=2;
     *else if final_hiv_status=1 and arv_evidence='Yes' and on_arv = 'No' then Final_ARV_Status=2;
    if final_hiv_status=1 and (on_arv="Yes" and arv_evidence = 'Yes') or (on_arv='Yes' and ever_taken_arv='Yes') then Final_ARV_Status=3;

    **Special Case, N=4***;
    if arv_evidence='Yes' and on_arv=' ' and ever_taken_arv=' ' then Final_ARV_Status=3; 


*Prev Result Known
  
  if recorded_hiv_result in ("POS" "NEG") or final_arv_status in (2 3) then prev_result_known = 1;
   else if result_recorded = "POS" and final_hiv_status = 0 then prev_result_known=0;
   else if result_recorded in ("NEG" "POS")  then prev_result_known=1;
   else prev_result_known=0;

*Prev Result
  if prev_result_known = 1 then do;
   if final_hiv_status = 0 then prev_result = "NEG";
   else if recorded_hiv_result = "POS" or result_recorded = "POS" or final_arv_status in (2 3)
     then prev_result = "POS";
    else prev_result = "NEG";
  end;

  else prev_result=" ";

*Prev Result Date
   
if prev_result_known = 1 then do; 
   prev_result_date=hiv_test_date;
   if hiv_test_date=. then prev_result_date=result_recorded_date; 
 end;


***Notes, 
   Self_Reported_Result= verbal_hiv_result (from table: bcpp_subject_hivtestinghistory)
   Has_tested=has_tested (from table: bcpp_subject_hivtestinghistory)
