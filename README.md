[![Build Status](https://travis-ci.org/botswana-harvard/bcpp-export.svg?branch=develop)](https://travis-ci.org/botswana-harvard/bcpp-export)

# bcpp_export

Export analysis datasets of Plot, Household, Enumeration and Participants data from the "BCPP" Edc.


    from bcpp_export.subjects import Subjects
    
    s = Subjects('bcpp-year-1', merge_on='household_member')
    
    # export to a csv file, default is "~/bcpp_export_subjects.csv"
    s.to_csv()
    
The exported dataframe is `pandas` dataframe:

    s.results
    
The exported dataframe, '`s.results` is a merge of all dataframes. Merge is a LEFT merge on `household_member`.

All dataframes in the class, with the exception of `results` are `pandas` dataframes and  prefixed are with `df_`.