#!/usr/bin/env python
# coding: utf-8

import os
import sys
import sqlite3
#import pandas as pd
#from sqlalchemy import create_engine
#from sqlalchemy import Table, Column, Integer, Numeric, Text, Date, ForeignKey, insert, MetaData
from PyQt5.QtSql import QSqlDatabase  # PyQt6 version crashes for me 
from PyQt5.QtSql import QSqlTableModel, QSqlRelation, QSqlRelationalTableModel
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QSpinBox


def createConnection(local_db_path):
    con = QSqlDatabase.addDatabase('QSQLITE')
    con.setDatabaseName(local_db_path)

    print(con.database())
    if not con.open():
        QMessageBox.critical(
            None,
            'QTableView Example - Error!',
            'Database Error: %s' % con.lastError().databaseText(),
        )
        
    return con

    
def show_table(local_db_path, table_name):
    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName(local_db_path)
    db.open()
    
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("My App")
            self.table = QTableView()
            self.model = QSqlTableModel(db=db)
            self.table.setModel(self.model)
            self.model.setTable(table_name)
            self.model.select()
            self.setMinimumSize(QSize(1024, 600))
            self.setCentralWidget(self.table)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()