#!/usr/bin/env python
# coding: utf-8

import os
import sys
import sqlite3
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, Numeric, Text, Date, ForeignKey, insert, MetaData


def make_db_sql(local_db_path):
    connection = sqlite3.connect(local_db_path)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS PixelVerification (recID INT, PID TEXT, imgDate TEXT, LC5 TEXT, LC25 TEXT)''')
    connection.commit()
    connection.close()

def make_LC_table_from_lut(lut, local_db_path, treat_existing):
    '''
    Creates sql pixel table in database location {local_db_path}
    Uses sqlite3 connection because this allows for assigmnet of primary key with pandas to_sql
    '''
    if isinstance(lut, pd.DataFrame):
        lcdf = lut[['LC_UNQ','LC5','LC25','USE_NAME']]
    else: 
        lcdf = pd.read_csv(lc_lut, usecols=['LC_UNQ','LC5','LC25','USE_NAME'])
        
    with sqlite3.connect(local_db_path) as con:
    
        lcdf.to_sql('LC', con=con, schema='public', if_exists=treat_existing, index = False, 
                 dtype= {
                    'LC_UNQ': 'INTEGER PRIMARY KEY',
                    'USE_NAME' : 'TEXT',
                    'LC5' : 'INTEGER',
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
            Column('recID', Integer(), primary_key=True),
            Column('PID', Text(), ForeignKey(pix_table.c.PID), nullable=False),
            Column('imgDate', Date(), nullable=False),
            Column('LC5', Integer(), ForeignKey('LC5.LC5id'), nullable=False),
            Column('LC', Integer(), ForeignKey(lc_table.c.LC_UNQ)),
            Column('HOMONBHD9', Integer(), nullable=False),
            Column('ForestProx', Integer()),
            Column('WaterProx', Integer()),
            Column('Notes', Text(255))
                )

        metadata.create_all(conn, checkfirst=True)
        print('added LC5 and PixVar tables to db')
        
def populate_LC5_table(engine):
    lc5_table = Table('LC5', MetaData(), autoload_with=engine)
    LC5Classes = [
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
        
