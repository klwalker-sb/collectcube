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
from PyQt5.QtGui import QFont
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
    QSpacerItem,
    QSizePolicy,
    QSpinBox,
    QAbstractSpinBox,
    QWidget,
    QMessageBox,
    QInputDialog
)
    
def open_obs_ui(local_db_path):
    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName(local_db_path)
    db.open()
    print('Tables in db: {}'.format(db.tables()))
    
    class Neighbor(QPushButton):
        def __init__(self,pid0):
            self.pid0 = pid0
            self.name = 'neighbor_{}'.format(pid0)
            super(Neighbor, self).__init__()
    
        def set_color(self,color):
            if color == 'white':
                self.setStyleSheet("QPushButton{background-color:white}")
            elif color == 'gray':
                self.setStyleSheet("QPushButton{background-color:lightgray}")
            elif color == 'yellow':
                self.setStyleSheet("QPushButton{background-color:yellow}")
                
    
    class MainWindow(QMainWindow):
        def __init__(self):

            super().__init__()
            
            main_layout = QVBoxLayout()
            main_layout_head1 = QHBoxLayout()
            main_layout_head1_left = QFormLayout()
            
            bigfont = QFont('Times', 14)
            
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
            self.imgdate_entry.setStyleSheet("QLineEdit{background-color:lightyellow}")
            main_layout_head1_left.addRow(QLabel("obs. date"), self.imgdate_entry)
            self.imgdate_entry.setFont(bigfont)
            self.imgdate_entry.editingFinished.connect(self.validate_date)
            
            main_layout_head1.addLayout(main_layout_head1_left)
            
            main_layout_head1_right = QVBoxLayout()
            goto_pid_button = QPushButton("Go to PID")
            main_layout_head1_right.addWidget(goto_pid_button)
            goto_pid_button.clicked.connect(self.goto_pid)
            add_pid_button = QPushButton("Add PID")
            main_layout_head1_right.addWidget(add_pid_button)
            #add_pid_button.clicked.connect(self.add_pid)
            
            main_layout_head1.addLayout(main_layout_head1_right)
            main_layout.addLayout(main_layout_head1)
           
            main_layout_head1b = QHBoxLayout()
            view_dates_button = QPushButton("View dates")
            main_layout_head1b.addWidget(view_dates_button)
            view_dates_button.clicked.connect(self.view_dates)
            add_date_button = QPushButton("Add date")
            main_layout_head1b.addWidget(add_date_button)
            add_date_button.clicked.connect(self.add_date)
            main_layout.addLayout(main_layout_head1b)
            
            main_layout_head2 = QFormLayout()
            
            ## linked landcover dropdowns (detailed lc categories shown once LC5 cat is selected): 
            self.lc_gen_picker = QComboBox()
            self.lc_gen_picker.setStyleSheet("QComboBox{background-color:lightyellow}")
            main_layout_head2.addRow(QLabel("Main Land cover"), self.lc_gen_picker)
            self.lc_gen_picker.setFont(bigfont) 

            self.lc_detail_picker = QComboBox()
            self.lc_detail_picker.setStyleSheet("QComboBox{background-color:lightyellow}")
            main_layout_head2.addRow(QLabel("Land Cover detail"), self.lc_detail_picker) 
            self.lc_detail_picker.setFont(bigfont)
            
            main_layout.addLayout(main_layout_head2)
            
            mid_layout = QHBoxLayout()
            #left_layout = QVBoxLayout()
            form = QFormLayout()
            form.setContentsMargins(60,60,-1,-1)
            
            main_layout_head1.addLayout(main_layout_head1_left)
            ##TODO: add pure box: if clicked, put 100 in corresponding box & grey out others
            self.built_entry = QLineEdit()
            form.addRow(QLabel("% BUILT"), self.built_entry)
            self.bare_entry = QLineEdit()
            form.addRow(QLabel("% BARE"), self.bare_entry)
            self.water_entry = QLineEdit()
            form.addRow(QLabel("% WATER"), self.water_entry)
            self.cropmono_entry = QLineEdit()
            form.addRow(QLabel("% MONO CROP LOW"), self.cropmono_entry)
            self.cropmix_entry = QLineEdit()
            form.addRow(QLabel("% MIXED CROPS"), self.cropmix_entry)
            self.lowveg_entry = QLineEdit()
            self.cropmed_entry = QLineEdit()
            form.addRow(QLabel("% MED CROPS"), self.cropmed_entry)
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
            self.stability_entry.addItems(["--","c - true change", "s - stable", "of - seasonal fluc.", 
                                     "rf - regular fluc. (tides)", "pi - positional instability"])
            form.addRow(QLabel("stability note"), self.stability_entry)
            self.state_entry = QComboBox()
            self.state_entry.addItems(["--","Bare","Young","Mature","Harvest","Burnt","Flooded","Deciduous-partial","Deciduous-full"])
            form.addRow(QLabel("current state"), self.state_entry)
            
            self.forestprox_entry = QLineEdit()
            form.addRow(QLabel("Proximity to forest edge"), self.forestprox_entry)
            self.waterprox_entry = QLineEdit()
            form.addRow(QLabel("Proximity to water"), self.waterprox_entry)
            self.percenttree_entry = QLineEdit()
            ## TODO: add image popup with examples
            form.addRow(QLabel("% TreeCover"), self.percenttree_entry)
            
            mid_layout.addLayout(form)
            
            left_spacer = QSpacerItem(40,40,QSizePolicy.Minimum,QSizePolicy.Expanding)
            mid_layout.addItem(left_spacer)
            
            right_layout = QVBoxLayout()
            right_layout.setContentsMargins(0,-1,100,0)
            
            placement_dict = {0:[1,1,1,1],1:[0,0,1,1],2:[0,1,1,1],3:[0,2,1,1],4:[1,0,1,1],
                              5:[1,2,1,1],6:[2,0,1,1],7:[2,1,1,1],8:[2,2,1,1]}
            neighborhood = QGridLayout()
            neighborhood.setSpacing(2)
            self.neighbors = {'neighbor_{}'.format(pid0): Neighbor(pid0=pid0) for pid0 in range(9)}
            for i in range(9):
                self.neighbors[f'neighbor_{i}'].setText(str(i))
                self.neighbors[f'neighbor_{i}'].setObjectName(self.neighbors[f'neighbor_{i}'].name)
                self.neighbors[f'neighbor_{i}'].setStyleSheet('QPushButton{border-color:black;border-width:2px}')
                self.neighbors[f'neighbor_{i}'].set_color('white')
                v = placement_dict[i]
                neighborhood.addWidget(self.neighbors[f'neighbor_{i}'],int(v[0]),int(v[1]),int(v[2]),int(v[3]))             
                self.neighbors[f'neighbor_{i}'].clicked.connect(self.add_neighbor)
            
            blanklabel0 = QLabel("   ")
            right_layout.addWidget(blanklabel0)
            blanklabel1 = QLabel("   ")
            right_layout.addWidget(blanklabel1)
            right_layout.addLayout(neighborhood)
            
            self.homonbhd9_entry = QSpinBox()
            self.homonbhd9_entry.setRange(0,8)
            self.homonbhd9_entry.setValue(8)
            self.homonbhd9_entry.setStyleSheet("QSpinBox{background-color:lightyellow}")
            self.homonbhd9_label = QLabel("Num neighbors with same LC: (note: only forcenter pixel)")
            self.homonbhd9_label.setGeometry(60, 30, 100, 50) 
            self.homonbhd9_label.setWordWrap(True) 
            
            right_layout.addWidget(self.homonbhd9_label)
            right_layout.addWidget(self.homonbhd9_entry)
            
            
            self.submit_neighbors_label = QLabel(
                "If all white boxes are the same lc as the center, click button below")
            self.submit_neighbors_label.setGeometry(60, 40, 100, 50) 
            self.submit_neighbors_label.setWordWrap(True) 
            
            right_layout.addWidget(self.submit_neighbors_label)
            submit_neighborhood_button = QPushButton("submit neighborhood")
            submit_neighborhood_button.clicked.connect(self.submit_neighborhood)
            right_layout.addWidget(submit_neighborhood_button)
            blanklabel2 = QLabel("   ")
            right_layout.addWidget(blanklabel2)
            blanklabel3 = QLabel("   ")
            right_layout.addWidget(blanklabel3)
            mid_layout.addLayout(right_layout)
            
            #right_spacer = QSpacerItem(100,40,QSizePolicy.Minimum,QSizePolicy.Expanding)
            #mid_layout.addItem(right_spacer)
            
            main_layout.addLayout(mid_layout)
            main_layout_foot = QFormLayout()
            
            self.notes_entry = QLineEdit()
            main_layout_foot.addRow(QLabel("Notes"), self.notes_entry)
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
            self.mapper.addMapping(self.cropmed_entry, 16)
            self.mapper.addMapping(self.lowveg_entry, 17)
            self.mapper.addMapping(self.dead_entry, 18)
            self.mapper.addMapping(self.medveg_entry, 19)
            self.mapper.addMapping(self.treeplant0_entry, 20)
            self.mapper.addMapping(self.highveg_entry, 21)
            self.mapper.addMapping(self.treeplant_entry, 22)
            self.mapper.addMapping(self.forest_entry, 23)
            self.mapper.addMapping(self.age_entry, 24)
            self.mapper.addMapping(self.stability_entry, 25)
            self.mapper.addMapping(self.state_entry, 26)
            self.mapper.addMapping(self.notes_entry, 27)
            
            self.model.select() 
            
            ## setting up relations with LC5 and LC tables to that text is seen but ints are stored

            self.lc_gen_relmodel = self.model.relationModel(lc5_index)
            self.lc_gen_picker.setModel(self.lc_gen_relmodel)
            self.lc_gen_picker.setModelColumn(self.lc_gen_relmodel.fieldIndex('LC5type'))
            self.lc_detail_relmodel = self.model.relationModel(lc_index)
            self.lc_detail_picker.setModel(self.lc_detail_relmodel)
            self.lc_detail_picker.setModelColumn(self.lc_detail_relmodel.fieldIndex('USE_NAME'))
            self.lc_gen_picker.currentIndexChanged.connect(self.update_lc_choices)
            
            self.mapper.toLast()

            self.setMinimumSize(QSize(250, 600))
            
            controls = QHBoxLayout()
  
            prev_rec = QPushButton("<")
            prev_rec.clicked.connect(self.mapper.toPrevious)
            next_rec = QPushButton(">")
            next_rec.clicked.connect(self.mapper.toNext)
            next_pix = QPushButton("next_pix")
            next_pix.clicked.connect(self.get_next_pix)
            save_rec = QPushButton("Save Changes")
            save_rec.clicked.connect(self.update_record)
            controls.addWidget(prev_rec)
            controls.addWidget(next_rec)
            controls.addWidget(next_pix)
            controls.addWidget(save_rec)
            
            #layout.addLayout(form)
            main_layout.addLayout(controls)
            
            widget = QWidget()
            widget.setLayout(main_layout)
            self.setCentralWidget(widget)

            self.color_neighborhood()
            
            
        #def initializeUI(self):
        def validate_date(self):
            passing = True
            date_entry = self.imgdate_entry.text()
            print('checking date entry: {}'.format(date_entry))
            try:
                day = date_entry.split('-')[2]
                mo = date_entry.split('-')[1]
                yr = date_entry.split('-')[0]
                if len(day) < 2 or len(mo) < 2 or len(yr) < 4:
                    passing = False
                if int(mo) > 12:
                    passing = False
                if int(yr) < 1950 or int(yr) > 2050:
                    passing = False
            except:
                passing = False
            if passing == False:
                msg = QMessageBox()
                msg.setWindowTitle("FORMATTING ERROR")
                msg.setIcon(QMessageBox.Warning)
                msg.setText("year format is YYYY-MM-DD")
                msg.exec_()
                return False
            else:
                print('formatting ok')
                return True
        
        
        def get_neighborhood_info(self):
            this_pid = self.pid_info.text()
            this_rec_id = self.recid_info.text()
            this_date = self.imgdate_entry.text()
            pid_qry = QSqlQuery("SELECT PID FROM PixelVerification WHERE PID0=? AND imgDate=?")
            pid_qry.bindValue(0,self.pid_info.text().split('_')[0])
            pid_qry.bindValue(1,this_date)
            pid_qry.exec()
            self.changed_neighbors = []
            while pid_qry.next():    
                self.changed_neighbors.append(pid_qry.value(0))
        
        
        def color_neighborhood(self):
            ## Color cells that have been done in neighborhood for same pid0 and date:
            for n, o in self.neighbors.items():
                o.set_color('white')
            self.get_neighborhood_info()
            #print(self.changed_neighbors) 
            changed_pid1s = [k.split('_')[1] for k in self.changed_neighbors] 
            for n, o in self.neighbors.items(): 
                if n.split('_')[1] in changed_pid1s:
                    o.set_color('gray')
                if n.split('_')[1] == self.pid_info.text().split('_')[1]:
                    o.set_color('yellow')
            
            
        def update_record(self):
            ## This just saves edits. Does not copy or move on from record, so no data checks yet.
            self.mapper.submit()
            this_pid = self.pid_info.text()
            this_rec_id = self.recid_info.text()
            this_date = self.imgdate_entry.text()
            self.color_neighborhood()  
            ## Fill in derived pid0 and pid1 attributes
            add_fields = QSqlQuery("UPDATE PixelVerification SET PID0=? PID1=? WHERE recID=?")
            add_fields.bindValue(0, this_rec_id)
            add_fields.bindValue(1, this_pid.split('_')[0])
            add_fields.bindValue(2, this_pid.split('_')[1])
            add_fields.exec()
            self.mapper.submit()
            
        
        def goto_pid(self):
            # pid can either be entered as single number(pid0) or as full pid(pid0_pid1)
            text, ok = QInputDialog().getText(self, "PID chooser",
                                     "PID:", QLineEdit.Normal)
            if ok and text:
                pid_qry = QSqlQuery("SELECT * from PixelVerification where PID = ?")
                if '_' in text:
                    pid_qry.bindValue(0, text)
                else:
                    pid0 = int(text)
                    pid_qry.bindValue(0, f'{pid0}_0')
                pid_qry.exec()
                pidmodel = QSqlQueryModel(self)
                pidmodel.setQuery(pid_qry)
                rec = pidmodel.record(0).value(0)
                #print('rec:{}'.format(rec))
                self.model.select()
                self.mapper.setCurrentIndex(rec)
                self.color_neighborhood()
            
            
        def check_data(self):
            # check date formatting:
            valid_date = self.validate_date()
            if valid_date == False:
                return False
            else:
                ## Check if any other key fields are blank:
                this_pid = self.pid_info.text()
                #print('pid:{}'.format(this_pid))
                this_lc = self.lc_detail_picker.currentText()
                #print('lc:{}'.format(this_lc))
                this_lc5 = self.lc_gen_picker.currentIndex()
                #print('lc5:{}'.format(this_lc5))
                
                if this_pid =='' or this_lc=='' or this_lc5==0:
                    msg = QMessageBox()
                    msg.setWindowTitle("MISSING DATA")
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("need to fill all yellow fields")
                    msg.exec_()
                
                    return False
            
                else:
                    ## Check if Land cover %s sum to 100:
                    per_built = self.built_entry.text()
                    per_bare = self.bare_entry.text()
                    per_water = self.water_entry.text()
                    per_cropm = self.cropmono_entry.text()
                    per_cropmix = self.cropmix_entry.text()
                    per_cropmed = self.cropmed_entry.text()
                    per_lowveg = self.lowveg_entry.text()
                    per_dead = self.dead_entry.text()
                    per_medveg = self.medveg_entry.text()
                    per_treeplant0 = self.treeplant0_entry.text()
                    per_highveg = self.highveg_entry.text()
                    per_treeplant = self.treeplant_entry.text()
                    per_forest = self.forest_entry.text()
                
                    lcs = [per_built,  per_bare, per_water, per_cropm, per_cropmix, per_cropmed, per_lowveg, 
                           per_dead, per_medveg, per_treeplant0, per_highveg, per_treeplant, per_forest]
                    areas = []
                    for r, lc in enumerate(lcs):
                        if lc != '':
                            areas.append(int(lc))
                    cum_area = sum(areas)
                    if cum_area != 100:
                        msg = QMessageBox()
                        msg.setWindowTitle("ADDITION FAILURE")
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("% Fields do not add up to 100")
                        msg.exec_()
                    
                        return False
                
                    else:
                        return True
        
        @QtCore.pyqtSlot(int)
        def update_lc_choices(self, i):
            #lc_code = self.lc5_relmodel.data(i,1)
            #print('pk is:{}'.format(pk))
            ## using display text instead of primary key for now. TODO: get above to work to use pk. 
            val = self.lc_gen_picker.itemText(i)
            query = QSqlQuery("SELECT * from LC where LC5_name = ?")
            query.addBindValue(val)
            query.exec_()
            self.model_lc_codes = QSqlQueryModel(self)
            self.model_lc_codes.setQuery(query)
            self.lc_detail_picker.setModel(self.model_lc_codes)
            ## reset index for future edits:
            self.lc_detail_picker.setCurrentIndex(0)  
    
        def get_next_pix(self):
            ## Save current row
            self.update_record()
            if self.check_data() == False:
                return False
            else:
                self.get_neighborhood_info
                if len(self.changed_neighbors) < 9:
                    print(len(self.changed_neighbors))
                    msg = QMessageBox()
                    msg.setWindowTitle("MISSING NEIGHBORS")
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("click on cells that are different or submit neighborhood (to copy/paste)")
                    msg.exec_()
                    return False
                    
                else:      
                    last_row = self.model.rowCount()
                    #print('there are {} records'.format(last_row))
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
                    self.color_neighborhood()
                        
                    return True
        
        def view_dates(self):
            self.date_model = QSqlTableModel()
            self.date_model.setTable("PixelVerification")
            self.date_table = QTableView()
            self.date_table.setModel(self.date_model)
            self.date_table.hideColumn(0)
            self.date_table.hideColumn(2)
            self.date_table.hideColumn(3)
            self.date_model.setFilter("PID = '{}'".format(self.pid_info.text()))
            self.date_model.select()
            self.date_table.setFixedWidth(1000)
            self.date_table.setFixedHeight(1000)
            ## sort on date column
            self.date_table.sortByColumn(4, Qt.AscendingOrder)
            self.date_table.show()
            
        def add_date(self):
            entry, ok = QInputDialog().getText(self, "date chooser",
                                     "Date:", QLineEdit.Normal)
            if ok and entry:
                ## Save current row
                self.mapper.submit()
                data_clean = self.check_data()
                if data_clean == False:
                    return False
            
                else:
                    ## Copy current record and place in temp table to change pk recID to next available record
                    this_rec_id = self.recid_info.text()
                    this_pid = self.pid_info.text()
                    this_date = self.imgdate_entry.text()
                    next_rec = self.model.rowCount()
                    #print('next record id = {}'.format(next_rec))
                    pid0 = this_pid.split('_')[0]
                    for i in range(9):
                        pid = f'{pid0}_{i}'
                        next_id = (next_rec+i)
                        new_date = entry
                        #print('pid: {}'.format(pid))
                        #print('next_id: {}'.format(next_id))
                        #print('new_date: {}'.format(new_date))
                        cpy_qry = QSqlQuery("CREATE TABLE tempTable AS SELECT * FROM PixelVerification WHERE PID=? AND imgDate=?")
                        cpy_qry.bindValue(0,pid)
                        cpy_qry.bindValue(1,this_date)
                        cpy_qry.exec()
                        fix_cpy_qry = QSqlQuery("UPDATE tempTable SET recID=?, imgDate=?")
                        fix_cpy_qry.bindValue(0,(next_id))
                        fix_cpy_qry.bindValue(1,new_date)
                        fix_cpy_qry.exec()
                        ## Paste record into pixel verificaiton table
                        QSqlQuery("INSERT INTO PixelVerification SELECT * FROM tempTable").exec()
                        QSqlQuery("DROP TABLE tempTable").exec()
      
                    self.mapper.submit()
                    self.model.select() 
                    self.mapper.toLast()
                    self.color_neighborhood()
                
                    ## If it did not succeed (there is no new record), probably because there are duplicate dates
                    ##    (this works because we get two records with the same recID and cannot insert them)
                    ##    warn user so they do not modify previous record
                    if self.recid_info.text() == this_rec_id:
                        msg = QMessageBox()
                        msg.setWindowTitle("DID NOT ADD RECORD")
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("check for duplicate dates")
                        msg.exec_()
                    
                        return False
                    else:
                        return True
                
                
        def add_neighbor(self):
            
            self.mapper.submit()
            data_clean = self.check_data()
            if data_clean == False:
                return False
            
            else:
                this_neighbor = int(self.sender().objectName().split('_')[1])
                print('copying record for neighbor {}'.format(this_neighbor))
                this_rec_id = self.recid_info.text()
                this_pid = self.pid_info.text()
                next_rec = self.model.rowCount()
                this_date = self.imgdate_entry.text()
                cpy_qry = QSqlQuery("CREATE TABLE tempTable AS SELECT * FROM PixelVerification WHERE PID=? AND imgDate=?")
                cpy_qry.bindValue(0,this_pid)
                cpy_qry.bindValue(1,this_date)
                cpy_qry.exec()
                new_pid = '{}_{}'.format(this_pid.split('_')[0],this_neighbor)
                check_qry = QSqlQuery("SELECT * FROM PixelVerification WHERE PID=? AND imgDate=?")
                check_qry.bindValue(0,new_pid)
                check_qry.bindValue(1,this_date)
                check_qry.exec()
                if check_qry.next():
                    msg = QMessageBox()
                    msg.setWindowTitle("DUPLICATE RECORD")
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("There is already a record in the db for this PID and date")
                    msg.exec_()
                    
                    return False
                
                else:
                    fix_cpy_qry = QSqlQuery("UPDATE tempTable SET recID=?, PID1=?, PID=?")
                    fix_cpy_qry.bindValue(0,next_rec)
                    fix_cpy_qry.bindValue(1,this_neighbor)
                
                    fix_cpy_qry.bindValue(2,new_pid)
                    fix_cpy_qry.exec()
                    ## Paste record into pixel verificaiton table and advance to record
                    QSqlQuery("INSERT INTO PixelVerification SELECT * FROM tempTable").exec()
                    QSqlQuery("DROP TABLE tempTable").exec()
      
                    self.mapper.submit()
                    self.model.select() 
                    self.mapper.toLast()
                    self.color_neighborhood()
                
                    if self.recid_info.text() == this_rec_id:
                        msg = QMessageBox()
                        msg.setWindowTitle("DID NOT ADD RECORD")
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("check for duplicate dates")
                        msg.exec_()
                    
                        return False
                    else:
                        return True
       
    
        def submit_neighborhood(self):
            
            data_clean = self.check_data()
            if data_clean == False:
                return False
            
            else:
                this_pid = self.pid_info.text()
                this_pid0 = self.pid_info.text().split('_')[0]
                cent_pid = f'{this_pid0}_0'
                next_rec = self.model.rowCount()
                this_date = self.imgdate_entry.text()
                self.get_neighborhood_info()
                changed_pid1s = [k.split('_')[1] for k in self.changed_neighbors]
                unchanged_pids = [f'{this_pid0}_{n}' for n in range(9) if str(n) not in changed_pid1s]
                ## check if unchanged cells and answer in box match:
                if len(unchanged_pids) != int(self.homonbhd9_entry.text()):
                    msg = QMessageBox()
                    msg.setWindowTitle("ENTRIES DO NOT MATCH")
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("check if there are more neighbors that do not match center or if number in box should be changed")
                    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Ignore)
                    retval = msg.exec_() 
                    ## retval=1048576 if ignore is selected
                    if retval != 1048576:
                        return False
                    
                else:
                    for row, value in enumerate (unchanged_pids):
                        cpy_qry = QSqlQuery("CREATE TABLE tempTable AS SELECT * FROM PixelVerification WHERE PID=? AND imgDate=?")
                        cpy_qry.bindValue(0,cent_pid)
                        cpy_qry.bindValue(1,this_date)
                        cpy_qry.exec()
                        fix_cpy_qry = QSqlQuery("UPDATE tempTable SET recID=?, PID1=?, PID=?")
                        fix_cpy_qry.bindValue(0,(next_rec+row))
                        pid1 = value.split('_')[1]
                        fix_cpy_qry.bindValue(1,pid1)
                        fix_cpy_qry.bindValue(2,value)
                        fix_cpy_qry.exec()
                        ## Paste record into pixel verificaiton table
                        QSqlQuery("INSERT INTO PixelVerification SELECT * FROM tempTable").exec()
                        QSqlQuery("DROP TABLE tempTable").exec()
            
                    self.mapper.submit()
            
                    ## return to center pixel:
                    pid_qry = QSqlQuery("SELECT * from PixelVerification where PID = ?")
                    pid_qry.bindValue(0, cent_pid)
                    pid_qry.exec()
                    pidmodel = QSqlQueryModel(self)
                    pidmodel.setQuery(pid_qry)
                    rec = pidmodel.record(0).value(0)
                    self.model.select()
                    self.mapper.setCurrentIndex(rec)
                    self.color_neighborhood()
                        
                    return True
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()