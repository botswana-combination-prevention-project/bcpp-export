*** create hh_status variable ***;
***per conversation with Lei, Erik, Molly on 05Sep2014, new HH_statuses are: not_enum_hh_ineligible, not_enum_never_there, not_enum_rarely_there,
   not_enum_seasonally_absent, not_enum_almost_always there, not_enum_unknown_status, not_enum_hoh_refused, enumerated_not enrolled, enrolled***;
 
 
 
***How many people in the house?***;
proc sort data=hh_member out=hh_member_count; by household_structure_id; run;
data hh_member_count;
set hh_member_count;
by household_structure_id;
Enumerated_HH_members+1;

if first.household_structure_id then Enumerated_HH_members=1;
if ~last.household_structure_id then delete;
if Enumerated_HH_members>0 then enum=1; else enum=0;

keep household_structure_id enumerated_hh_members enum;

run;
 
***did anyone enroll?***;
proc sort data=HH_member_status; by household_structure_id; run;
data HH_member_status; set HH_member_status; count=0; if member_status='BHS' then count=1; run;
data HH_member_status; set HH_member_status; by household_structure_id; sum+count; if first.household_structure_id then sum=count;
if sum>0 then status1='Enrolled'; run;
 
 
proc sort data=hh_refused; by household_structure_id; run;
data HH_member_status; merge HH_member_status hh_refused (in=a); by household_structure_id; if a then do; status2='HOH Refused'; drop hh_status; end; run;
proc sort data=HH_member_status; by household_structure_id; proc sort data=HH_status; by household_structure_id;
proc sort data=hh_log out=hh_log2; where household_status ~=' '; by household_structure_id; run;
 
data HH_member_status; merge HH_status (drop=created modified) HH_member_status (drop=created)  hh_member_count hh_log2;
      by household_structure_id; format status $35.;
      status3=eligibles_last_seen_home; status4=household_status; status=status1; if status1=' ' then status=status2; if status2=' '  and status1=' ' then status=status3;
       if status1=' '  and status2=' ' and status3=' ' then status=status4; status=propcase(status);
       if enum=1 then status='Enumerated not Enrolled';
      if status1='Enrolled' or status2='Enrolled' or status3='Enrolled' or status4='Enrolled' then status='Enrolled';       
         if household_status='refused' then status='HOH Refused';
       if status='Hoh Refused' then status='HOH Refused';
      run;
