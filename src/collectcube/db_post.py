#!/usr/bin/env python
# coding: utf-8

import os
import sys
import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
import numpy as np


def open_data_records_sqlachemy(local_db_path):
    engine = create_engine('sqlite:///'+ local_db_path)
    with engine.connect() as con:
        df = pd.read_sql_table('PixelVerification', con)
    df['PIDi']=df.apply(lambda x: '{:07d}_{}'.format(int(x.PID0),x.PID1),axis=1)
    df.drop(['PID'],axis=1,inplace=True)

    return df

def open_pix_info_sqlachemy(local_db_path):
    engine = create_engine('sqlite:///'+ local_db_path)
    with engine.connect() as con:
        pix = pd.read_sql_table('pixels', con)
    pix.drop(['PID0','PID1'],axis=1,inplace=True)

    return pix

def allow_lc_transitions(row):
    normal_trans = {11:[56,66],56:[66],45:[46,54],46:[54],17:[57],57:[77],65:[80],52:[65]}
    normal_fluct = {7:[17,57,77],17:[7],57:[7],77:[7]}
    
    nat_change = 0
    if row['LC_pre'] in normal_trans.keys():
        if row['LC_post'] in normal_trans[row['LC_pre']]:
            nat_change = 1
    if row['LC_pre'] in normal_fluct.keys():
        if row['LC_post'] in normal_fluct[row['LC_pre']]:
            nat_change = 1
                
    return nat_change

def get_internal_homogeneity(row,name_col,keep_nodata):
    row.fillna(0, inplace=True)
    
    classlc = str(row[name_col])
    
    if classlc.startswith('Mixed') or classlc in ['Grass_tree-mix', 'Tree-Water_mix','77','51','9','18','19']:
        h = 999
    elif classlc == 'NoVeg_Bare' or classlc == '2':
        h = row['BARE']
    elif classlc == 'NoVeg_Built' or classlc == '3':   
        h = row['BUILT']
    elif classlc == 'NoVeg_Water' or classlc == '7':    
        h = row['WATER']
    elif classlc == 'NoVeg' or classlc == '1':
        h = row['BARE'] + row['BUILT'] + row['WATER']
    elif classlc.startswith('Grass') or classlc in ['12','13','15','17']:
        h = row['GRASS']
    elif classlc == 'Crops-Orchard-new' or classlc == '45':
         h = row['CROPMED'] + row['TREEPLANT0']
    elif classlc in ['Crops-Orchard','Crops-Banana','Crops-Yerba-Mate','Crops-Med_forest',
                              'Crops-Vineyard','D_Crop_Med','Crop_Med','40','41','42','43','44','45','46','47']:
        h = row['CROPMED']
    elif classlc in ['L-Crops-Low', 'Crops-Low', 'Crops-Soybeans', 'Crops-Wheat', 'Crops-Rice','Crops-Sugar',
                     '30','31','22','33','37','38']:
        h = row['CROPMONO']
    elif classlc in ['M_Crops-mix','Crops-mix','35','23','24','25','26','32','34','36','39'] or classlc.startswith('Crop'):
        h = row['CROPMIX'] + row['CROPMONO'] + row['CROPMED']
    elif classlc in ['TreePlant-new','NewPlant','11']:
        h = row['TREEPLANT0']
    elif classlc in ['Shrub','MedVeg_wet','52','57']:
        h = row['MEDVEG'] + row['HIGHVEG']
    elif classlc == 'Trees-Orchard-closed' or classlc == '54':
        h = row['CROPMED'] + row['TREEPLANT'] + row['FOREST']
    elif classlc.startswith('TreePlant') or classlc in ['56','66','60']:    
        h = row['TREEPLANT']
    elif classlc.startswith('Tree') or classlc in['64','65','67','68','80']:
        h = row['FOREST'] + row['HIGHVEG']
    elif classlc in ['Cleared','Burnt-woody','58','10']:
        h = row['DEAD'] + row['BARE']
    elif classlc in ['N_NoCrop', 'NoCrop', 'no_crop', '98']:
        h = 1 - (row['CROPMIX'] + row['CROPMONO'] + row['CROPMED'])
    elif classlc == 'LowVeg' or classlc == '20':
        h = row['GRASS'] + row['CROPMONO'] + row['CROPMIX'] + row['TREEPLANT0']    
    elif classlc == 'unknown' or classlc == '99':
        h = 0
    else:
        print(f'{classlc} is not in LUT')
        h = 0
    
    if keep_nodata == True:
        if h == 0:
            h = 999
    
    return int(h)

def get_sample_for_date(target_date,local_db_path,sample_type,sample_cats,lut):
    '''
    date should be YYYY-MM-DD, but can be YYYY
    sample_type = 'area_est' ## 'area_est',  validation', 'training' 
    sample_cats = 'bi_crop'   ## 'bi_tree', 'bi_forest'
    '''
    if len(str(target_date))==4:
        target_yr = target_date
        target_date = f'{target_yr}-06-01'
    else:
        target_yr = target_date[:4]
       
    sample_date = pd.Timestamp(target_date)
    
    df = open_data_records_sqlachemy(local_db_path)
    df['obs_type']='direct'
    df['HOMOINT']= df.apply(lambda row : get_internal_homogeneity(row,'LC',True), axis=1)
        
    # Copy LC column before modifying it
    df['LC_UNQ'] = df['LC']
    
    if sample_cats not in ['crop_type','LC25']:
        if sample_cats not in ['crop4']:
            df['LC'] = df.apply(lambda x: 30 if ((x['LC']>=30) & (x['LC']<48)) else x['LC'],axis=1)
            df['LC'] = df.apply(lambda x: 80 if ((x['LC']>=60) & (x['LC']<90)) else x['LC'],axis=1)
            df['LC'] = df.apply(lambda x: 98 if ((x['LC']<30) | ((x['LC']>=48) & (x['LC']<60))) else x['LC'],axis=1)

    df_direct = df[(df['imgDate']>f'{target_yr-1}-06-01')&(df['imgDate']<f'{target_yr}-06-01')]
    
    keep_columns = ['recID','PIDi','LC5','LC','LC_UNQ','HOMONBHD9', 'Stability','imgDate']
    ## for each PID, get min obs after sample date
    df_post = df[df['imgDate']>=sample_date]
    min_value = df_post.groupby('PIDi')['imgDate'].min()
    df_post = df_post.merge(min_value, on='PIDi',suffixes=('', '_min'))
    df_post = df_post[df_post['imgDate']==df_post['imgDate_min']].drop('imgDate_min', axis=1)
    df_post = df_post[keep_columns]

    ## for each PID, get max obs before sample date
    df_pre = df[df['imgDate']<sample_date]
    max_value = df_pre.groupby('PIDi')['imgDate'].max()
    df_pre = df_pre.merge(max_value, on='PIDi',suffixes=('', '_max'))
    df_pre = df_pre[df_pre['imgDate']==df_pre['imgDate_max']].drop('imgDate_max', axis=1)
    df_pre = df_pre[keep_columns]

    df_prepost = pd.merge(df_pre,df_post,on='PIDi',how='outer',suffixes=('_pre','_post'))
    df_prepost['obsgap'] = df_prepost['imgDate_post'] - df_prepost['imgDate_pre']
    df_prepost['change5'] = df_prepost['LC5_post'] - df_prepost['LC5_pre']
    df_prepost['changeLC'] = df_prepost['LC_post'] - df_prepost['LC_pre']
    ## remove NaN from LC_post columns (change to -1) and convert doubles back to integers to match LUT
    df_prepost['LC5_post'].fillna(-1, inplace=True)
    df_prepost['LC5_post'] = df_prepost.apply(lambda x: int(x['LC5_post']),axis=1)
    df_prepost['LC_post'].fillna(-1, inplace=True)
    df_prepost['LC_post'] = df_prepost.apply(lambda x: int(x['LC_post']),axis=1)
    
    lut = pd.read_csv(lut)
    lut_keep=['LC_UNQ','Stability']
    lut = lut[lut_keep]
    prepost = pd.merge(df_prepost, lut, left_on='LC_post', right_on='LC_UNQ', how='left')
    
    ## create flag for natural LC fluctuations to allow such cases to be kept (but possibly filtered to exclude from validation etc.)  
    prepost['nat_fluct'] = prepost.apply(lambda row: allow_lc_transitions(row), axis=1)
    
    prepost['LC5'] = prepost.apply(lambda x: x['LC5_post'] if
        ((x['change5'] == 0) or (x['nat_fluct'] == 1)) and 
        (pd.Timedelta(x['Stability']*365, unit='d') > x['obsgap']) else -1, axis=1)
    prepost['LC'] = prepost.apply(lambda x: x['LC_post'] if
        ((x['changeLC'] == 0) or (x['nat_fluct'] == 1)) and 
         (pd.Timedelta(x['Stability']*365, unit='d') > x['obsgap']) else -1, axis=1)
    
    ## if forest and observed within 8 yrs after date, keep as forest (even if no pre-date obs)
    prepost['LC5'] = prepost.apply(lambda x: 70 if (x['LC_post']>=70) and (x['LC_post']<90) and
                                   (x['imgDate_post']-sample_date < pd.Timedelta(8*365, unit='d')) else x['LC5'], axis=1)    
    prepost['LC'] = prepost.apply(lambda x: x['LC_post'] if (x['LC_post']>=70) and (x['LC_post']<90) and
                                   (x['imgDate_post']-sample_date < pd.Timedelta(8*365, unit='d')) else x['LC'], axis=1)
     
    ## if trees and observed within 5 yrs after date, keep as forest (even if no pre-date obs)
    prepost['LC5'] = prepost.apply(lambda x: 70 if  (x['LC_post']>60) and (x['LC_post']<70) and
                                  (x['imgDate_post']-sample_date < pd.Timedelta(5*365, unit='d')) else x['LC5'], axis=1) 
    prepost['LC'] = prepost.apply(lambda x: x['LC_post'] if  (x['LC_post']==65) and
                                   (x['imgDate_post']-sample_date < pd.Timedelta(5*365, unit='d')) else x['LC'], axis=1) 
    
    ## if noCrop and observed within 3 yrs after date, keep as noCrop (even if no pre-date obs)
    prepost['LC5'] = prepost.apply(lambda x: 99 if  (x['LC_post']==98) and
                                  (x['imgDate_post']-sample_date < pd.Timedelta(5*365, unit='d')) else x['LC5'], axis=1) 
    prepost['LC'] = prepost.apply(lambda x: x['LC_post'] if  (x['LC_post']==98) and
                                   (x['imgDate_post']-sample_date < pd.Timedelta(5*365, unit='d')) else x['LC'], axis=1)
   
     ## if stable category and observed within 2 yrs before date, keep as is (even if no post-date obs)
    #prepost['LC5'] = prepost.apply(lambda x: 10 if  (x['LC_pre']==10) and
    #                              (-sample_date - x['imgDate_pre'] < pd.Timedelta(500, unit='d')) else x['LC5'], axis=1) 
    #prepost['LC'] = prepost.apply(lambda x: x['LC_pre'] if  ((x['LC_pre']==7 or x['LC_pre']==3)) and
    #                               (x['imgDate_post']-sample_date < pd.Timedelta(500, unit='d')) else x['LC'], axis=1)
    
    ##TODO: add age and planted forest calcs
    ##TODO: add regrowth
    
    prepost=prepost[prepost['LC']>0]
    prepost['obs_type'] = 'indirect'
    prepost['imgDate_pre'].fillna(value=pd.Timestamp('1900-01-01'))
    prepost['recID'] = prepost.apply(lambda x: x['recID_pre'] if
                                     (sample_date-x['imgDate_pre'] < x['imgDate_post']-sample_date) else x['recID_post'], axis=1)   
 
    prepost_cols=['recID','LC','LC5','obs_type','nat_fluct']
    df_cols = df.columns.difference(prepost_cols).tolist()
    df_cols.append('recID')
    df_indirect = pd.merge(prepost[prepost_cols], df[df_cols],on='recID',how='left')
    all_obs = pd.concat([df_direct, df_indirect], axis=0)
    all_obs = all_obs.sort_values('PIDi')
    all_obs.drop_duplicates('PIDi', inplace=True)
    print(f'there are {all_obs.shape[0]} observations for selected date')
    
    pixdf = open_pix_info_sqlachemy(local_db_path)
    pix_data = pd.merge(all_obs,pixdf,left_on='PIDi',right_on='PID',how='left')
    ## format to meet specs used in LUCinSA_helpers
    pix_data.rename(columns={"PID0": "OID_", "cent_X": "XCoord", "cent_Y":"YCoord"})
    pix_data['LC2'] = pix_data.apply(lambda x: 30 if x['LC'] == 30 else 0, axis=1)
    
    if sample_type == 'validation' or sample_type == 'area_est':
        center_obs = pix_data[pix_data['PID1']==0]
        print(f'there are {center_obs.shape[0]} center pixel observations')
        return center_obs
    else:
        return pix_data
                                  

def prioritize_row(row):
    if (row['doubt_CNC'] == 1) or (row['doubt_LC'] == 1) or (row['doubt_LC5'] == 1):
        priority = 3
    if (row['LC25_name'] == 'NoVeg_Built') & (row['sampgroup'] != 'rd_samp') & (row['source'] == 'GE'):
        priority = 1
    elif (row['LC25_name'] == 'NoVeg_Bare') & (row['sampgroup'] != 'rd_samp') & (row['source'] == 'GE'):
        priority = 1
    elif (str(row['LC25_name']).startswith('Crops')) & (row['biome'] == 'Chaco'):
        priority = 1
    elif (row['source'] == 'GE') & (row['entry_lev'] > 1):
        priority = 2
    else:
        priority = 3
    
    return priority
        
    
def balance_training_data(yr, lut, pixdf, out_dir, cutoff, mix_factor):
    '''
    balances class samples based on map proportion, relative to sample size for class with max map proportion
    (this estimated map proportion is a column named "perLC25E" in the LUT )
    allows a minimum threshold to be set {cutoff} so that sample sizes are not reduced below the minimum
    allows a factor to be set for mixed (heterogeneous) classes to sample them more heavily than main classes
    (the maximum value will depend on the available samples for these classes.)
    '''
    
    if isinstance(lut, pd.DataFrame):
        lut = lut
    else:
        lut=pd.read_csv(lut)
        
    if isinstance(pixdf, pd.DataFrame):
        pixdf = pixdf
    else:
        pixdf = pd.read_csv(pixdf)
        
    if 'LC25_name' not in pixdf:
        pixdf = pixdf.merge(lut[['LC_UNQ','USE_NAME','LC25','LC25_name','perLC25E']], left_on='LC', right_on='LC_UNQ', how='left')

    ## add internal pixel homogeneity:  this is now done above
    #pixdf['HOMOINT'] = pixdf.apply(lambda row : get_internal_homogeneity(row,'LC25_name',True), axis=1) 
    ##TODO: Add optional filters here if desired -- but for training probably best to include impure data
    
    ## Allow only one pixel per neighborhood per class:
    pixdf = pixdf.sort_values('HOMOINT', ascending=False).drop_duplicates(subset=['PID0', 'LC25_name'])
    ##TODO: consider alternatives to taking only pixel with highest internal purity
    
    ## get estimated class percents (this is estimated from other maps and in column in LUT)
    classprev = lut.sort_values('perLC25E')[["perLC25E", "LC25_name"]]
    classprev= classprev.dropna()
    classprev = classprev.drop_duplicates(subset = "perLC25E") 
    tot = classprev["perLC25E"].sum()
    print("tot percent =:", tot)     # should be 1
   
    ## get highest class percent
    mmax = classprev["perLC25E"].max()
    ## convert all class percents to ratio of highest
          ## (keeping all samples from mmax class (n), n = mmax * TotalSamp  -> TotalSamp = n/mmax )
    classprev["perLC25E"] = classprev["perLC25E"]/mmax
    ## get number of samples for each class
    counts = pixdf['LC25_name'].value_counts().reset_index()
    counts.columns = ['LC25_name', 'counts']
    print(counts)
    counts.set_index('LC25_name',inplace=True)
    print(f'Total sample size before balancing is: {sum(counts["counts"])}')

    ## Separate highest quality sample to select from first 
    pixdf['priority'] = pixdf.apply(lambda row : prioritize_row(row), axis=1) 
    p1_pixdf = pixdf[pixdf['priority'] == 1]
    p1_counts = p1_pixdf['LC25_name'].value_counts().reset_index()
    p1_counts.columns = ['LC25_name', 'p1_counts']
    p1_counts.set_index('LC25_name',inplace=True)
    p2_pixdf = pixdf[pixdf['priority'] == 2]
    p2_counts = p2_pixdf['LC25_name'].value_counts().reset_index()
    p2_counts.columns = ['LC25_name', 'p2_counts']
    p2_counts.set_index('LC25_name',inplace=True)
    all_counts = pd.concat([counts,p1_counts,p2_counts],axis=1)
    all_counts['p1_counts'].fillna(0,inplace=True)
    all_counts['p2_counts'].fillna(0,inplace=True)
    
    ratiodf = classprev.merge(all_counts, left_on="LC25_name", right_on="LC25_name", how='left')
    maxsamp = ratiodf.at[ratiodf['perLC25E'].idxmax(), 'counts']
    print(f'samp size for class with max proportion is {maxsamp}')
    ##  Get resample ratio based on class proportion. if existing samples are < cutoff, keep all samples. 
    ##    Otherwise reduce according to proportion, but do not allow to go below cutoff
    ##    Allow for separate treatment of mixed classes based on mix_factor
    
    mixed_classes = ["Mixed-VegEdge", "Mixed-path", "Crops-mix"]
    ratiodf['ratios'] = np.where(ratiodf["LC25_name"].isin(mixed_classes),(mix_factor * ratiodf["perLC25E"] * maxsamp / ratiodf["counts"]),
                           np.where(ratiodf["counts"] < cutoff, 1, 
                              np.where(ratiodf["perLC25E"] * maxsamp < ratiodf["counts"], 
                                 np.maximum((cutoff/ratiodf["counts"]), (ratiodf["perLC25E"] * maxsamp / ratiodf["counts"])),   
                            1)))
    
    #ratiodf['ratios'] = np.where(ratiodf["LC25_name"].isin(mixed_classes), (ratiodf['ratios'] * mix_factor), ratiodf['ratios'])
    
    ratiodf['p1_draw'] =  np.where( ratiodf['p1_counts'] == 0, 0, 
                                   np.where(ratiodf['p1_counts'] <= ratiodf['counts'] * ratiodf['ratios'], 1,  
                                            (ratiodf['ratios']*ratiodf['counts'])/ratiodf['p1_counts']))
    ratiodf['p2_draw'] =  np.where( ratiodf['p2_counts'] == 0, 0,
                                   np.where(ratiodf['p1_counts'] + ratiodf['p2_counts'] < ratiodf['counts'] * ratiodf['ratios'], 1,
                                            (ratiodf['ratios']*ratiodf['counts'] - ratiodf['p1_counts']) / ratiodf['p2_counts'])) 
    ratiodf['p3_draw'] =  np.where(ratiodf['p2_counts'] + ratiodf['p2_counts'] >  ratiodf['counts'] * ratiodf['ratios'], 0,
                                   (ratiodf['ratios']*ratiodf['counts'] - (ratiodf['p1_counts']+ratiodf['p2_counts']))/ (ratiodf['counts'] - (ratiodf['p1_counts']+ratiodf['p2_counts'])))
                                   
                                   
    print(ratiodf)
    ## Use random column to select samples (already in df here, for easy reproduction, but could make new ran column from 0-1)
    pixdf_ratios = pixdf.merge(ratiodf[['LC25_name','ratios','p1_draw','p2_draw','p3_draw']],
                               left_on="LC25_name", right_on="LC25_name", how='left')
    p1_samp = pixdf_ratios[(pixdf_ratios['priority'] == 1) & (pixdf_ratios['rand'] < pixdf_ratios['p1_draw'])]
    p2_samp = pixdf_ratios[(pixdf_ratios['priority'] == 2) & (pixdf_ratios['rand'] < pixdf_ratios['p2_draw'])]
    p3_samp = pixdf_ratios[(pixdf_ratios['priority'] == 3) & (pixdf_ratios['rand'] < pixdf_ratios['p3_draw'])]
    full_samp = pd.concat([p1_samp,p2_samp,p3_samp],axis=0)
    print(full_samp['LC25_name'].value_counts())
    totsamp = sum(full_samp['LC25_name'].value_counts())
    print(f'Total sample size after balancing is: {totsamp}')
    
    pixdf_path = os.path.join(out_dir,f'{yr-1}pixdf_bal{cutoff}_mix{mix_factor}.csv')
    pd.DataFrame.to_csv(pixdf_ratios, pixdf_path)
    
    return pixdf_ratios
