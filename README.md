[![Build Status](https://travis-ci.org/botswana-harvard/bcpp-export.svg?branch=develop)](https://travis-ci.org/botswana-harvard/bcpp-export)

# bcpp_export

Export analysis datasets of Plot, Household, Enumeration and Participants data from the "BCPP" Edc.

From the python shell

    from bcpp_export.dataframes.combined_data_frames import CombinedDataFrames
    dfs = CombinedDataFrames('bcpp-year-1')
    dfs.to_csv()    

.. or, if you wish to inspect the individual objects first:

    from bcpp_export.dataframes.load_all import load_all
    from bcpp_export.dataframes.combined_data_frames import CombinedDataFrames

    objects = load_all('bcpp-year-1')
    members = objects.get('members_object')
    subjects = objects.get('subjects_object')
    residences = objects.get('residences_object')

    # then when you are ready ...    
    dfs = CombinedDataFrames('bcpp-year-1', **objects)
    dfs.to_csv()    

Each object contains dataframes. The important ones are: 
    
    df_members = members.results  # all enumerated residents
    df_subjects = subjects.results  # all participating residents
    df_residences = residences.residences  # merge of household and plot info
    df_plots = residences.plots
    df_housholds = residences.households

Each dataframe can be written to CSV as can any pandas dataframe:

    df_members = members.results
    df_members.to_csv('~/tmp/members.csv', index=False)

But each object can help with exporting the dataframe to CSV by setting a few defaults before exporting:

     members.to_csv()
     # creates ~/bcpp_export_<YYYYMMDD>_members.csv
     
You can change the target folder:

    members.to_csv(export_folder='~/Documents/bcpp/exports')
    # creates ~/Documents/bcpp/exports/bcpp_export_<YYYYMMDD>_members.csv

The dataframe exported is filtered by `pairs` and intervention `arms`. The default is set on the class attributes:

    default_export_pairs = range(1, 16)
    default_export_arms = (INTERVENTION, )
    
But you can change this when calling `to_csv`, for example:

     from bcpp_export.dataframes.csv_export_mixin import INTERVENTION, NON_INTERVENTION 
     
     members.to_csv(export_arms=(INTERVENTION, NON_INTERVENTION), export_pairs=range(1, 8))

 If you wanted to see the filtered dataframe, call `filtered_export_dataframe` directly:
 
     filtered_df = members.filtered_export_dataframe(
         export_arms=(INTERVENTION, NON_INTERVENTION), export_pairs=range(1, 4))
     filtered_df.groupby('pair').size()

     pair
        1      320
        2      233
        3     1009

     filtered_df.groupby('intervention').size()

     intervention
        0     800
        1     762

Also:
* Default pd.merge is a LEFT merge on `household_member`.
* Attributes of "private" dataframes are prefixed with `df_` 
* Uses BCPP Edc 1.11.117, see requirements.txt.

## Example for CDC Export
    
    from bcpp_export.dataframes import load_all, CDCDataFrames
    
    objects = load_all()
    dfs = CDCDataFrames('bcpp-year-1', **objects)
    dfs.to_csv()
    
or just:

    dfs = CDCDataFrames('bcpp-year-1')
    dfs.to_csv()

## identity256
The dataframes are passed `django` model `values_list`. Encrypted field values (e.g. PII) are not decrypted by `django` for `values_lists`. To include a `sha256` representation of the personal identifier specify `add_identity256=True` when instantiating the `Subjects` class. Ensure the settings attribute `KEYPATH` points to the valid encryption keys. 
    
    IMPORTANT: the value of identity256 is not encrypted so the dataset should be considered sensitive.

    >>> s = Subjects('bcpp-year-1', merge_on='household_member', add_identity256=True)
    >>> s.results['identity256'][0] = '6d24639a6bd16765f3518d2e67146eb5950a7a05b6c8956e639423ac1042da74'

## Other Examples

### Add column based on external viral load data

    import pandas as pd
 
    df = pd.read_csv(os.path.expanduser('~/bcpp_export_subject_cpc_1-13.csv'))
    vl = pd.read_csv('~/Downloads/Viral_Load_ids.csv')
    vl['vl_drawn'] = 1
    df1 = pd.merge(df, vl, how='left', on='subject_identifier')
    options = dict(
        na_rep='',
        encoding='utf8',
        date_format='%Y-%m-%d %H:%M:%S',
        path_or_buf=os.path.expanduser('~/bcpp_export_subject_cpc_1-13.csv'))
    df1.to_csv(**options)
    
    # or directly on the household class from above (h)
    
    vl = pd.read_csv('~/Downloads/Viral_Load_ids.csv')
    vl['vl_drawn'] = 1
    h.subjects = pd.merge(h.subjects, vl, how='left', on='subject_identifier')    
    h.subjects['vl_drawn'] = h.subjects.apply(
        lambda row: 0 if row['final_hiv_status'] == 1 and pd.isnull(row['vl_drawn']) else row['vl_drawn'], axis=1)
    h.to_csv('subjects', columns=columns, index=False)
