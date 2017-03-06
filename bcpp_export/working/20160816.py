import pandas as pd
import numpy as np

from collections import namedtuple

df['community'] = df.apply(lambda row: community(row['community']), axis=1)

Community = namedtuple('Community', 'code name pair intervention')

htc_communities_map = {
    'Bokaa': 'bokaa',
    'Digawana': 'digawana',
    'Gumare': 'gumare',
    'Gweta': 'gweta',
    'Lentswelatau': 'lentswelatau',
    'Lentsweletau': 'lentsweletau',
    'Lerala': 'lerala',
    'Letlhakeng': 'letlhakeng',
    'Lorwana': 'digawana',
    'Mandunyane': 'mandunyane',
    'Masunga': 'masunga',
    'Mathangwane': 'mathangwane',
    'Maunatlala': 'maunatlala',
    'Metsimotlhabe': 'metsimotlhabe',
    'Mmadinare': 'mmadinare',
    'Mmankgodi': 'mmankgodi',
    'Mmathethe': 'mmathethe',
    'Molapowabojang': 'molapowabojang',
    'Nata': 'nata',
    'Nkange': 'nkange',
    'Oodi': 'oodi',
    'Otse': 'otse',
    'Rakops': 'rakops',
    'Ramokgonami': 'ramokgonami',
    'Ranaka': 'ranaka',
    'Sebina': 'sebina',
    'Sefhare': 'sefhare',
    'Sefophe': 'sefophe',
    'Shakawe': 'shakawe',
    'Shoshong': 'shoshong',
    'Tati Siding': 'tati_siding',
    'Tsetsebjwe': 'tsetsebjwe',
}

communities = {
    'bokaa': Community('17', 'bokaa', 4, False),
    'digawana': Community('12', 'digawana', 1, True),
    'gumare': Community('35', 'gumare', 13, True),
    'gweta': Community('34', 'gweta', 12, True),
    'lentsweletau': Community('16', 'lentsweletau', 3, True),
    'lerala': Community('21', 'lerala', 6, True),
    'letlhakeng': Community('15', 'letlhakeng', 3, False),
    'masunga': Community('37', 'masunga', 15, True),
    'mathangwane': Community('31', 'mathangwane', 11, True),
    'maunatlala': Community('23', 'maunatlala', 7, True),
    'metsimotlhabe': Community('29', 'metsimotlhabe', 9, False),
    'mmadinare': Community('26', 'mmadinare', 8, False),
    'mmandunyane': Community('32', 'mmandunyane', 11, False),
    'mmankgodi': Community('19', 'mmankgodi', 5, True),
    'mmathethe': Community('20', 'mmathethe', 5, False),
    'molapowabojang': Community('13', 'molapowabojang', 2, False),
    'nata': Community('38', 'nata', 15, False),
    'nkange': Community('27', 'nkange', 10, True),
    'oodi': Community('18', 'oodi', 4, True),
    'otse': Community('14', 'otse', 2, True),
    'rakops': Community('33', 'rakops', 12, False),
    'ramokgonami': Community('24', 'ramokgonami', 7, False),
    'ranaka': Community('11', 'ranaka', 1, False),
    'sebina': Community('28', 'sebina', 10, False),
    'sefhare': Community('39', 'sefhare', 14, True),
    'sefophe': Community('22', 'sefophe', 6, False),
    'shakawe': Community('36', 'shakawe', 13, False),
    'shoshong': Community('25', 'shoshong', 8, True),
    'tati_siding': Community('30', 'tati_siding', 9, True),
    'tsetsebjwe': Community('40', 'tsetsebjwe', 14, False)
}


def htc_community(htc_community):
    htc_community = str(htc_community).strip()
    try:
            return htc_communities_map[htc_community]
    except (KeyError):
            return htc_community


def intervention(row):
    """Return 1 for intervention communities, otherwise 0."""
    if pd.isnull(row['community']) or row['community'] not in communities:
            return np.nan
    return 1 if communities.get(row['community']).intervention else 0


def pair(row):
    if pd.isnull(row['community']) or row['community'] not in communities:
        return np.nan
    return communities.get(row['community']).pair


def final_hiv_status(row):
    test = None if pd.isnull(row['hiv_test_result']) else row['hiv_test_result']
    self_report = None if pd.isnull(row['self_report_hiv_test_result']) else row['self_report_hiv_test_result']
    previous_test = None if pd.isnull(row['prior_hiv_test_result']) else row['prior_hiv_test_result']
    return test or previous_test or self_report or 'N/A'

# raw PIMS df
df_pims = pd.read_csv('/Users/erikvw/source/bcpp-rdb/media/upload/pims_haart_2016-07-31-1556110254860200.csv')

# raw HTC df
df_htc = pd.read_csv('/Users/erikvw/source/bcpp-rdb/media/upload/htc_2016-07-31-153406.657744+0200.csv')
df_htc['final_hiv_status'] = df_htc.apply(lambda row: final_hiv_status(row), axis=1)
df_htc = df_htc.rename(columns={'omang_nbr': 'identity256', 'rdbcalculatedage': 'age', 'community_name': 'community', 'interview_date': 'report_date'})


df = pd.merge(df_htc, df_pims, on='identity256', how='left', suffixes=['', '_pims'])
df['linked'] == df[pd.isnull(df['final_hiv_status'])]['artcurrentpatientprogramstatusdescr']

# BCPP
bhs = pd.read_csv('/Users/erikvw/Documents/bcpp/rdb_bhs.csv', low_memory=False)
# HTC
df1 = pd.read_csv('/Users/erikvw/Documents/bcpp/rdb_df1.csv', low_memory=False)
# PIMS
df2 = pd.read_csv('/Users/erikvw/Documents/bcpp/rdb_df2.csv', low_memory=False)

df = pd.read_csv('/Users/erikvw/Documents/bcpp/rdb_df.csv', low_memory=False)

# fill null communities with PIMS clinic name if source is PIMS
df['community'] = df.apply(lambda row: row['pimsclinicname'] if row['source'] == 'pims' else row['community'], axis=1)
# convert to standard community names
df['community'] = df.apply(lambda row: htc_community(row['community']), axis=1)
# add pair for each community
df['pair'] = df.apply(lambda row: pair(row), axis=1)
# add intervention or non-intervention for each community
df['intervention'] = df.apply(lambda row: intervention(row), axis=1)

#
df[(df['dupl'] == False) & (df['intervention'] == True) & (df['final_hiv_status'] == 'HIV+')].groupby('community').size()
df[(df['dupl'] == False) & (df['intervention'] == True) & (df['final_hiv_status'] == 'HIV+')].groupby(['community', 'source']).size()
