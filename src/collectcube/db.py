#!/usr/bin/env python
# coding: utf-8

import os
import sys
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy import Table, Column, Integer, Numeric, Text, Date, ForeignKey, insert, MetaData


def make_db_sql(local_db_path):
    ## NOT USING THIS CURRENTLY
    connection = sqlite3.connect(local_db_path)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS PixelVerification (recID INT, PID TEXT, imgDate TEXT, LC5 TEXT, LC25 TEXT)''')
    connection.commit()
    connection.close()


def make_pixel_table_in_db(pixdf, local_db_path, treat_existing):
    '''
    Creates sql pixel table in database location {local_db_path}
    Uses sqlite3 connection because this allows for assigmnet of primary key with pandas to_sql
    '''
    with sqlite3.connect(local_db_path) as con:
    
        pixdf.to_sql('pixels', con=con, if_exists=treat_existing, index = False, 
                 dtype= {
                    'PID': 'TEXT PRIMARY KEY',
                    'PID0': 'INTEGER',
                    'PID1': 'INTEGER',
                    'Center' : 'INTEGER',
                    'cent_lat' : 'REAL',
                    'cent_lon' : 'REAL',
                    'cent_X' : 'REAL', 
                    'cent_Y' : 'REAL',
                    'ransamp' : 'INTEGER',
                    'sampgroup' : 'TEXT',
                    'checked' : 'INTEGER'
                 }                
                ) 
    con.close()
    
def make_LC_table_from_lut(lut, local_db_path, treat_existing):
    '''
    Creates sql pixel table in database location {local_db_path}
    Uses sqlite3 connection because this allows for assigmnet of primary key with pandas to_sql
    '''
    if isinstance(lut, pd.DataFrame):
        lcdf = lut[['LC_UNQ','LC5', 'LC5_name','LC25','USE_NAME']]
    else: 
        lcdf = pd.read_csv(lut, usecols=['LC_UNQ','LC5','LC5_name','LC25','USE_NAME'])
        
    with sqlite3.connect(local_db_path) as con:
    
        lcdf.to_sql('LC', con=con, schema='public', if_exists=treat_existing, index = False, 
                 dtype= {
                    'LC_UNQ': 'INTEGER PRIMARY KEY',
                    'USE_NAME' : 'TEXT',
                    'LC5' : 'INTEGER',
                    'LC5_name' : 'TEXT',
                    'LC25' : 'INTEGER'
                 }                
                ) 
    con.close()
    
def make_main_support_tables(engine):
    metadata = MetaData()
    with engine.connect() as conn:
        pix_table = Table('pixels', metadata, autoload_with=engine)
        lc_table = Table('LC', metadata, autoload_with=engine)
       
        LC5 = Table('LC5', metadata,
            Column('LC5id', Integer(), primary_key=True),
            Column('LC5type', Text()) 
                  )
              
        PixVar = Table('PixelVerification', metadata,
            Column('recID', Integer(), primary_key=True, autoincrement=True),
            Column('PID', Text(), ForeignKey(pix_table.c.PID), nullable=False),
            Column('PID0', Integer(), ForeignKey(pix_table.c.PID0), nullable=False),
            Column('PID1', Integer(), ForeignKey(pix_table.c.PID1), nullable=False),
            Column('imgDate', Date()),
            Column('LC5', Integer(), ForeignKey('LC5.LC5id')),
            Column('LC', Integer(), ForeignKey(lc_table.c.LC_UNQ)),
            Column('HOMONBHD9', Integer()),
            Column('ForestProx', Integer()),
            Column('WaterProx', Integer()),
            Column('PercentTree', Integer()),
            Column('BUILT', Integer()),
            Column('BARE', Integer()),
            Column('WATER', Integer()),
            Column('CROPMONO', Integer()),
            Column('CROPMIX', Integer()),
            Column('CROPMED', Integer()),
            Column('GRASS', Integer()),
            Column('DEAD', Integer()),
            Column('MEDVEG', Integer()),
            Column('TREEPLANT0', Integer()),
            Column('HIGHVEG', Integer()),
            Column('TREEPLANT', Integer()),
            Column('FOREST', Integer()),
            Column('Age', Text()),
            Column('Stability', Text()),
            Column('State', Text()),
            Column('Notes', Text(255))
                )

        metadata.create_all(conn, checkfirst=True)
        print('added LC5 and PixVar tables to db')
        
def populate_LC5_table(engine):
    lc5_table = Table('LC5', MetaData(), autoload_with=engine)
    LC5Classes = [
         { 'LC5id': '0',
          'LC5type' : ' ------'
         },
        
         { 'LC5id': '10',
          'LC5type' : 'NoVeg'
         },
         { 'LC5id': '20',
          'LC5type' : 'LowVeg'
         },
         { 'LC5id': '40',
          'LC5type' : 'MedVeg'
         },
         { 'LC5id': '50',
          'LC5type' : 'HighVeg'
         },
         { 'LC5id': '70',
          'LC5type' : 'Trees'
         },
         { 'LC5id': '99',
          'LC5type' : 'Unknown'
         }
         ]

    with engine.connect() as con:
        ins = lc5_table.insert()
        con.execute(ins, LC5Classes)
        con.commit()
    con.close()

def make_db(db_path):
    sql_db_path = 'sqlite:///'+ db_path
    engine = create_engine(sql_db_path, echo=False)
    make_main_support_tables(engine)
    populate_LC5_table(engine)
    
def get_max_id_in_db(db_path,extra_pix=None):
    ## First check max id in db:
    sql_db_path = 'sqlite:///'+ db_path
    engine = create_engine(sql_db_path, echo=False)
    with engine.connect() as conn:
        if inspect(engine).has_table('PixelVerification'):
            df = pd.read_sql_table('PixelVerification', conn)
            p_max = df['PID0'].max()
        else:
            p_max = -1
        if inspect(engine).has_table('pixels'):   
            df2 = pd.read_sql_table('pixels', conn)
            p_max2 = df2['PID0'].max()
        else:
            p_max2 = -1
            
    ## Now check max id in pt_file:
    if extra_pix == None:
        p_max3 = -1
    elif isinstance(extra_pix, gpd.GeoDataFrame):
        p_max3 = extra_pix['PID0'].max()    
    else:
        pix = gpd.read_file(extra_pix)
        p_max3 = pix['PID0'].max()
    
    pid_max = max(p_max,p_max2,p_max3)
    
    return pid_max

## Check that Table was made (and read back as pandas dataframe)
def check_table(local_db_path,tablex):
    sql_db_path = 'sqlite:///' + local_db_path
    engine = create_engine(sql_db_path, echo=False)
    with engine.connect() as conn:
        df = pd.read_sql_table(tablex, con=cnx)
        print(df.tail())
    conn.close()

    return df

def delete_record_sqlite(local_db_path, pid):
    conn = sqlite3.connect(local_db_path)
    cursor = conn.cursor()
    try:
        sql_del = cursor.execute(f"DELETE FROM PixelVerification WHERE PID = '{pid}'")
        print("Total records affected: ", sql_del.rowcount)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Oops! Something went wrong. Error: {e}")
        # reverse the change in case of error
        conn.rollback()