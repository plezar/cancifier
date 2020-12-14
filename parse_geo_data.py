import pandas as pd
import numpy as np
import GEOparse
from os import listdir
from os.path import isfile, join
import traceback

norm_files = [f for f in listdir('./data/normal/') if isfile(join('./data/normal/', f))]
rm = [i.split('_')[0] for i in norm_files] + ['GSE10893']

data_info = pd.read_excel('dataset_information.xlsx')
gse_ids = [i for i in np.unique(data_info['Dataset_id'].values) if 'GSE' in i]

for i in rm:
    gse_ids.remove(i)

sample_ids = np.unique(data_info['Sample_id'])

geo_data = pd.DataFrame()

for geo_id in gse_ids:
    gse = GEOparse.get_GEO(geo=geo_id, destdir="./data/raw/")
    mtx = pd.DataFrame()
    try:
        for gpl_name, gpl in gse.gpls.items():
            gb_acc = gpl.table.set_index('ID')['GB_ACC']
            break

        for gsm_name, gsm in gse.gsms.items():
            if gsm_name in sample_ids:
                val = pd.DataFrame()
                val[gsm_name] = gsm.table.set_index('ID_REF')['VALUE']
                mtx = pd.concat([mtx, val], axis=1)

    except Exception:
        traceback.print_exc()
        with open('failed_gse_ids.txt', mode='a') as failed:
            failed.write('{}\n'.format(geo_id))
        continue

    # Quantile normalization
    # https://stackoverflow.com/questions/37935920/quantile-normalization-on-pandas-dataframe
    rank_mean = mtx.astype('float64').stack().groupby(mtx.astype('float64').rank(method='first').stack().astype(int)).mean()
    mtx = mtx.astype('float64').rank(method='min').stack().astype(int).map(rank_mean).unstack()

    mtx['GB_ACC'] = gb_acc
    mtx = mtx.dropna()
    mtx['GB_ACC'] = [i.split('.')[0] for i in mtx['GB_ACC'].values]
    mtx['median'] = mtx.iloc[:,:-1].median(axis=1).values
    mtx = mtx.sort_values(by=['median'], ascending=False)
    mtx = mtx.drop_duplicates(subset=['GB_ACC'], keep='first')
    mtx = mtx.sort_index().drop('median', axis=1)
    mtx = mtx.set_index('GB_ACC')
    mtx.to_csv('./data/normal/{}_normalized.txt.gz'.format(geo_id), index=True, compression='gzip', sep='\t')

# Concatenating the resulting matrices

matrices = ['./data/normal/'+f for f in listdir('./data/normal') if isfile(join('./data/normal/', f))]

conc_data = pd.DataFrame()

for n, file in enumerate(matrices):
    
    mtx = pd.read_csv(file, sep='\t', index_col=[0])
    batch = pd.DataFrame(columns=list(mtx.columns))
    batch.loc['batch'] = [file.split('_')[0].split('/')[3] for i in np.arange(len(mtx.columns))]
    mtx = mtx.append(batch)
    conc_data = pd.concat([conc_data, mtx], axis=1, sort=False)

conc_data.to_csv('./data/normal/HCMDB_normalized_merged.txt.gz', index=True, compression='gzip', sep='\t')


######
conc_data = pd.read_csv('./data/normal/HCMDB_normalized_merged.txt.gz', sep='\t', index_col=[0])
#conc_data = conc_data[~conc_data.index.duplicated(keep=False)]
conc_data = conc_data[conc_data.index.notnull()]

conc_data['missing'] = conc_data.isnull().sum(axis=1).values
conc_data.loc['missing'] = conc_data.isnull().sum(axis=0).values

# giving column label
# dropping column
conc_data = conc_data.sort_values(by=['missing'], axis=0, ascending=True).drop('missing', axis=1)

conc_data = conc_data.sort_values(by=['missing'], axis=1, ascending=True).drop('missing', axis=0)

conc_data['missing'] = conc_data.isnull().sum(axis=1).values
conc_data.loc['missing'] = conc_data.isnull().sum(axis=0).values

conc_data = conc_data.head(60000)


conc_data.to_csv('./data/normal/HCMDB_normalized_merged_60000by_nan.txt.gz', index=True, compression='gzip', sep='\t')



