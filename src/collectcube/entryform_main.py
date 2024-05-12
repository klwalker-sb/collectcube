#!/usr/bin/env python
# coding: utf-8

import os
import sys
import sqlite3
#import pandas as pd
#from sqlalchemy import create_engine
#from sqlalchemy import Table, Column, Integer, Numeric, Text, Date, ForeignKey, insert, MetaData
from PyQt5.QtSql import QSqlDatabase  # PyQt6 version crashes for me 
from PyQt5.QtSql import QSqlTableModel, QSqlRelation, QSqlRelationalTableModel, QSqlRelationalDelegate, QSqlQuery, QSqlQueryModel
from PyQt5 import QtCore
from PyQt5.QtCore import QSize, Qt, QSortFilterProxyModel
from PyQt5.QtWidgets import (
    QApplication,
    QTableView,
    QComboBox,
    QDataWidgetMapper,
    QDateTimeEdit,
    QFormLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QSpinBox,
    QAbstractSpinBox,
    QWidget
)

    
def open_obs_ui(local_db_path):
    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName(local_db_path)
    db.open()
    print('Tables in db: {}'.format(db.tables()))
  
    class MainWindow(QMainWindow):
        def __init__(self):

            super().__init__()
            
            main_layout = QVBoxLayout()
            main_layout_head1 = QHBoxLayout()
            main_layout_head1_left = QFormLayout()
            
            ## recID is the primary key for the table. it autoincrements and is hidden.
            self.recid_info = QLineEdit()
            main_layout_head1_left.addRow(QLabel("rec_id"), self.recid_info)
            self.recid_info.setDisabled(True)
            
            ## PID is a string primary ID. PID0 and PID1 are int components
            ## TODO: set checked = 1 for pixel with same PID when form is closed (relation table)
            self.pid_info = QLineEdit()
            main_layout_head1_left.addRow(QLabel("PID"), self.pid_info)
            self.recid_info.setDisabled(True)
            
            self.imgdate_entry = QLineEdit()
            main_layout_head1_left.addRow(QLabel("obs. date"), self.imgdate_entry)
            
            main_layout_head1.addLayout(main_layout_head1_left)
            
            main_layout_head1_right = QVBoxLayout()
            goto_PID_button = QPushButton("Go to PID")
            main_layout_head1_right.addWidget(goto_PID_button)
            #goto_PID_button.clicked.connect(self.mapper.goto_PID)
            add_pid_button = QPushButton("Add PID")
            main_layout_head1_right.addWidget(add_pid_button)
            #add_pid_button.clicked.connect(self.mapper.add_pid)
            add_date_button = QPushButton("Add date")
            main_layout_head1_right.addWidget(add_date_button)
            #add_date_button.clicked.connect(self.mapper.add_date)
            
            main_layout_head1.addLayout(main_layout_head1_right)
            main_layout.addLayout(main_layout_head1)
           
            main_layout_head2 = QFormLayout()
            ## linked landcover dropdowns (detailed lc categories shown once LC5 cat is selected): 
            self.lc_gen_picker = QComboBox()
            main_layout_head2.addRow(QLabel("Main Land cover"), self.lc_gen_picker)

            self.lc_detail_picker = QComboBox()
            main_layout_head2.addRow(QLabel("Land Cover detail"), self.lc_detail_picker) 
            
            main_layout.addLayout(main_layout_head2)
            
            mid_layout = QHBoxLayout()
            #left_layout = QVBoxLayout()
            form = QFormLayout()
            
            main_layout_head1.addLayout(main_layout_head1_left)
            ##TODO: add pure box: if clicked, put 100 in corresponding box & grey out others
            self.built_entry = QLineEdit()
            form.addRow(QLabel("% BUILT"), self.built_entry)
            self.bare_entry = QLineEdit()
            form.addRow(QLabel("% BARE"), self.bare_entry)
            self.water_entry = QLineEdit()
            form.addRow(QLabel("% WATER"), self.water_entry)
            self.cropmono_entry = QLineEdit()
            form.addRow(QLabel("% MONO CROP"), self.cropmono_entry)
            self.cropmix_entry = QLineEdit()
            form.addRow(QLabel("% MIXED CROPS"), self.cropmix_entry)
            self.lowveg_entry = QLineEdit()
            form.addRow(QLabel("% Other LOW VEG"), self.lowveg_entry)
            self.dead_entry = QLineEdit()
            form.addRow(QLabel("% DEAD WOODY"), self.dead_entry)
            self.medveg_entry = QLineEdit()
            form.addRow(QLabel("% MED VEG"), self.medveg_entry)
            self.treeplant0_entry = QLineEdit()
            form.addRow(QLabel("% ORCHARD"), self.treeplant0_entry)
            self.highveg_entry = QLineEdit()
            form.addRow(QLabel("% TALL WOODY"), self.highveg_entry)
            self.treeplant_entry = QLineEdit()
            form.addRow(QLabel("% TREE PLANTATION"), self.treeplant_entry)
            self.forest_entry= QLineEdit()
            form.addRow(QLabel("% FOREST"), self.forest_entry)
            self.age_entry=QLineEdit()
            form.addRow(QLabel("Estimated Age"), self.age_entry)
            self.stability_entry = QComboBox()
            form.addRow(QLabel("stability note"), self.stability_entry)
            self.state_entry = QComboBox()
            self.state_entry.addItems(["--","Bare","Young","Mature","Harvest","Burnt","Flooded","Deciduous-partial","Deciduous-full"])
            form.addRow(QLabel("current state"), self.state_entry)
            
            self.forestprox_entry = QLineEdit()
            form.addRow(QLabel("Proximity to forest edge (optional)"), self.forestprox_entry)
            self.waterprox_entry = QLineEdit()
            form.addRow(QLabel("Proximity to watere (optional)"), self.waterprox_entry)
            self.percenttree_entry = QLineEdit()
            ## TODO: add image popup with examples
            form.addRow(QLabel("% TreeCover"), self.percenttree_entry)
            
            #left_layout.addLayout(form)
            mid_layout.addLayout(form)
            
            right_layout = QVBoxLayout()
            
            neighborhood = QGridLayout()
            neighborhood.setSpacing(3)
            button_PID1_1 = QPushButton("1")
            #button_PID1_1.clicked.connect(self.mapper.add_PID1(1))
            neighborhood.addWidget(button_PID1_1,0,0,1,1)
            button_PID1_2 = QPushButton("2")
            #button_PID1_1.clicked.connect(self.mapper.add_PID1(2))
            neighborhood.addWidget(button_PID1_2,0,1,1,1)
            button_PID1_3 = QPushButton("3")
            #button_PID1_1.clicked.connect(self.mapper.add_PID1(3))
            neighborhood.addWidget(button_PID1_3,0,2,1,1)
            button_PID1_4 = QPushButton("4")
            #button_PID1_1.clicked.connect(self.mapper.add_PID1(4))
            neighborhood.addWidget(button_PID1_4,1,0,1,1)
            button_PID1_0 = QPushButton("0")
            neighborhood.addWidget(button_PID1_0,1,1,1,1)
            button_PID1_5 = QPushButton("5")
            #button_PID1_1.clicked.connect(self.mapper.add_PID1(5))
            neighborhood.addWidget(button_PID1_5,1,2,1,1)
            button_PID1_6 = QPushButton("6")
            #button_PID1_1.clicked.connect(self.mapper.add_PID1(6))
            neighborhood.addWidget(button_PID1_6,2,0,1,1)
            button_PID1_7 = QPushButton("7")
            #button_PID1_1.clicked.connect(self.mapper.add_PID1(7))
            neighborhood.addWidget(button_PID1_7,2,1,1,1)
            button_PID1_8 = QPushButton("8")
            #button_PID1_1.clicked.connect(self.mapper.add_PID1(8))
            neighborhood.addWidget(button_PID1_8,2,2,1,1)
            
            right_layout.addLayout(neighborhood)
            
            self.homonbhd9_entry = QSpinBox()
            self.homonbhd9_entry.setRange(0,8)
            self.homonbhd9_entry.setValue(8)
            #"Num neighbors with same LC"
            right_layout.addWidget(self.homonbhd9_entry)
            
            mid_layout.addLayout(right_layout)
            
            main_layout.addLayout(mid_layout)
            main_layout_foot = QFormLayout()
            
            self.notes_entry = QLineEdit()
            main_layout_foot.addRow(QLabel("Notes (optional)"), self.notes_entry)
            main_layout.addLayout(main_layout_foot)
            
            self.model = QSqlRelationalTableModel(db=db)
            self.model.setTable('PixelVerification')
            
            lc5_index = self.model.fieldIndex("LC5") # column of main table in which LC5 variable is stored
            lc_index = self.model.fieldIndex("LC") # column of main table in which LC variable is stored
            self.model.setRelation(lc5_index, QSqlRelation('LC5','LC5id','LC5type')) # (table, id to store, value to show)
            self.model.setRelation(lc_index, QSqlRelation('LC','LC_UNQ','USE_NAME')) # (table, id to store, value to show)
            
            self.mapper = QDataWidgetMapper()
            self.mapper.setModel(self.model)
            self.mapper.setItemDelegate(QSqlRelationalDelegate())
            self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
            
            self.mapper.addMapping(self.recid_info, 0)
            self.mapper.addMapping(self.pid_info, 1)
            #self.mapper.addMapping(self.pid0_entry, 2)
            #self.mapper.addMapping(self.pid1_entry, 3)
            self.mapper.addMapping(self.imgdate_entry, 4)
            
            self.mapper.addMapping(self.lc_gen_picker, lc5_index)
            self.mapper.addMapping(self.lc_detail_picker, lc_index)
            self.mapper.addMapping(self.homonbhd9_entry, 7)
            self.mapper.addMapping(self.forestprox_entry, 8)
            self.mapper.addMapping(self.waterprox_entry, 9)
            self.mapper.addMapping(self.percenttree_entry, 10)
            self.mapper.addMapping(self.built_entry, 11)
            self.mapper.addMapping(self.bare_entry, 12)
            self.mapper.addMapping(self.water_entry, 13)
            self.mapper.addMapping(self.cropmono_entry, 14)
            self.mapper.addMapping(self.cropmix_entry, 15)
            self.mapper.addMapping(self.lowveg_entry, 16)
            self.mapper.addMapping(self.dead_entry, 17)
            self.mapper.addMapping(self.medveg_entry, 18)
            self.mapper.addMapping(self.treeplant0_entry, 19)
            self.mapper.addMapping(self.highveg_entry, 20)
            self.mapper.addMapping(self.treeplant_entry, 21)
            self.mapper.addMapping(self.forest_entry, 22)
            self.mapper.addMapping(self.age_entry, 23)
            self.mapper.addMapping(self.stability_entry, 24)
            self.mapper.addMapping(self.state_entry, 25)
            self.mapper.addMapping(self.notes_entry, 26)
            
            
            #self.model.setEditStrategy(QSqlTableModel.OnRowChange)
            ## setting up relations with LC5 and LC tables to that text is seen but ints are stored
            
            ## populate fields for displayed recID
            #self.mapper.setCurrentIndex(0)
            ## populate model
            self.model.select() 
            
            self.lc_gen_relmodel = self.model.relationModel(lc5_index)
            self.lc_gen_picker.setModel(self.lc_gen_relmodel)
            self.lc_gen_picker.setModelColumn(self.lc_gen_relmodel.fieldIndex('LC5type'))
            self.lc_detail_relmodel = self.model.relationModel(lc_index)
            self.lc_detail_picker.setModel(self.lc_detail_relmodel)
            self.lc_detail_picker.setModelColumn(self.lc_detail_relmodel.fieldIndex('USE_NAME'))
            self.lc_gen_picker.currentIndexChanged.connect(self.update_lc_choices)
            
            self.mapper.toLast()

            self.setMinimumSize(QSize(1024, 600))
            
            controls = QHBoxLayout()
  
            prev_rec = QPushButton("<")
            prev_rec.clicked.connect(self.mapper.toPrevious)
            next_rec = QPushButton(">")
            next_rec.clicked.connect(self.mapper.toNext)
            next_pix = QPushButton("next_pix")
            next_pix.clicked.connect(self.get_next_pix)
            save_rec = QPushButton("Save Changes")
            save_rec.clicked.connect(self.submit_changes)
            controls.addWidget(prev_rec)
            controls.addWidget(next_rec)
            controls.addWidget(next_pix)
            controls.addWidget(save_rec)
            
            #layout.addLayout(form)
            main_layout.addLayout(controls)
            
            widget = QWidget()
            widget.setLayout(main_layout)
            self.setCentralWidget(widget)
            
        #def initializeUI(self):
               
        @QtCore.pyqtSlot(int)
        def update_lc_choices(self, i):
            #lc_code = self.lc5_relmodel.data(i,1)
            #print('pk is:{}'.format(pk))
            ## using display text instead of primary key for now. TODO: get above to work to use pk. 
            val = self.lc_gen_picker.itemText(i)
            query = QSqlQuery()
            query.prepare("SELECT * from LC where LC5_name = ?")
            query.addBindValue(val)
            query.exec_()
            self.model_lc_codes = QSqlQueryModel(self)
            self.model_lc_codes.setQuery(query)
            self.lc_detail_picker.setModel(self.model_lc_codes)
            ## reset index for future edits:
            self.lc_detail_picker.setCurrentIndex(0)  
    
        def submit_changes(self):
            self.mapper.submit()
            #self.model.submitAll()
            #self.mapper.setCurrentIndex(0)
            #self.layoutChanged.emit()
    
        def get_next_pix(self):
            ## Save current row
            self.mapper.submit()
            last_row = self.model.rowCount()
            print('there are {} records'.format(last_row))
            # Find the last row and add a new record
            id_query = QSqlQuery()
            id_query.prepare("SELECT recID, MAX(PID0) FROM PixelVerification")
            id_query.exec()
            if id_query.next() is None:
                pid0 = 1
            else:
                print('query return {}'.format(id_query.value(1)))
                pid0 = id_query.value(1) + 1
            pid = "{}_0".format(pid0)
            add_query = QSqlQuery()
            add_query.prepare("INSERT INTO PixelVerification (PID, PID0, PID1, LC5, LC)"
                              "VALUES( ?, ?, ?, ?, ?)")
            add_query.bindValue(0, pid)
            add_query.bindValue(1, pid0)
            add_query.bindValue(2, 0)
            add_query.bindValue(3, 0)
            add_query.bindValue(4, 0)
            add_query.exec()
            self.mapper.submit()
            self.model.select() 
            self.mapper.toLast()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()