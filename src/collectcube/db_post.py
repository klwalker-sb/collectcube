#!/usr/bin/env python
# coding: utf-8

import os
import sys
import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine


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
    df['obs_type']='direct_GE'
    
    if sample_cats not in ['crop_type','LC25']:
        if sample_cats not in ['crop4']:
            df['LC'] = df.apply(lambda x: 30 if ((x['LC']>=30) & (x['LC']<50)) else x['LC'],axis=1)
            df['LC'] = df.apply(lambda x: 80 if ((x['LC']>=60) & (x['LC']<90)) else x['LC'],axis=1)
            df['LC'] = df.apply(lambda x: 98 if ((x['LC']<30) | ((x['LC']>=50) & (x['LC']<60))) else x['LC'],axis=1)

    # TODO: incorporate pixel purity

    df_direct = df[(df['imgDate']>f'{target_yr-1}-06-01')&(df['imgDate']<f'{target_yr}-06-01')]

    keep_columns = ['recID','PIDi','LC5','LC','Stability','imgDate']
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

    df_prepost = pd.merge(df_pre,df_post,on='PIDi',how='left',suffixes=('_pre','_post'))
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
    prepost['LC5'] = prepost.apply(lambda x: x['LC5_post'] if (
        (x['change5'] == 0) and (pd.Timedelta(x['Stability']*365, unit='d') > x['obsgap'])) else -1, axis=1)
    prepost['LC'] = prepost.apply(lambda x: x['LC_post'] if (
        (x['changeLC'] == 0) and (pd.Timedelta(x['Stability']*365, unit='d') > x['obsgap'])) else -1, axis=1)
    prepost=prepost[prepost['LC']>0]
    prepost['obs_type'] = 'indirect_GE'
    prepost['recID'] = prepost.apply(lambda x: x['recID_pre'] 
                                     if sample_date-x['imgDate_pre'] < x['imgDate_post']-sample_date else x['recID_post'], axis=1)   

    prepost_cols=['recID','LC','LC5','obs_type']
    df_cols = df.columns.difference(prepost_cols).tolist()
    df_cols.append('recID')
    df_indirect = pd.merge(prepost[prepost_cols], df[df_cols],on='recID',how='left')
    all_obs = pd.concat([df_direct, df_indirect], axis=0)
    all_obs = all_obs.sort_values('PIDi')
    all_obs.drop_duplicates('PIDi', inplace=True)
    print(f'there are {all_obs.shape[0]} observations for selected date')
    center_obs = all_obs[all_obs['PID1']==0]
    print(f'there are {center_obs.shape[0]} center pixel observations')
           
    return all_obs