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
    QCheckBox,
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
    
def open_obs_ui(local_db_path, entry_lev):
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
            main_layout_head1a = QHBoxLayout()
            main_layout_head1ar = QHBoxLayout()
            main_layout_head1al = QHBoxLayout()
            main_layout_head1 = QHBoxLayout()
            main_layout_head1_left = QFormLayout()
            
            bigfont = QFont('Times', 13)
            
            ## recID is the primary key for the table. it autoincrements and is hidden.
            self.recid_info = QLineEdit()
            rec_lab = QLabel(self.recid_info)
            rec_lab.setText("rec_id:")
            main_layout_head1al.addWidget(rec_lab)
            main_layout_head1al.addWidget(self.recid_info)
            self.recid_info.setDisabled(True)
            main_layout_head1a.addLayout(main_layout_head1al)
            
            self.entry_lev_info = QLineEdit()
            entry_lab = QLabel(self.entry_lev_info)
            entry_lab.setText("rec_entry_lev:")
            main_layout_head1ar.addWidget(entry_lab)
            main_layout_head1ar.addWidget(self.entry_lev_info)
            self.entry_lev_info.setDisabled(True)
            main_layout_head1a.addLayout(main_layout_head1ar)
            
            main_layout.addLayout(main_layout_head1a)
            
            ## PID is a string primary ID. PID0 and PID1 are int components
            ## TODO: set checked = 1 for pixel with same PID when form is closed (relation table)
            self.pid_info = QLineEdit()
            main_layout_head1_left.addRow(QLabel("PID"), self.pid_info)
            self.pid0_entry = QLineEdit()
            #main_layout_head1_left.addRow(QLabel("PID0"), self.pid0_entry)
            #self.recid_info.setDisabled(True)
            
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
            add_pid_button.clicked.connect(self.add_pid)
            
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
            self.lc_gen_picker.setFont(bigfont) 
            main_layout_head2.addRow(QLabel("Main Land cover"), self.lc_gen_picker)
            if entry_lev > 1:
                self.lc_gen_picker.setStyleSheet("QComboBox{background-color:lightyellow}")
            else:
                self.lc_gen_picker.setDisabled(True)
                
            self.lc_detail_picker = QComboBox()
            self.lc_detail_picker.setStyleSheet("QComboBox{background-color:lightyellow}")
            self.lc_detail_picker.setFont(bigfont)
            main_layout_head2.addRow(QLabel("Land Cover detail"), self.lc_detail_picker) 
            
            main_layout.addLayout(main_layout_head2) 
            
            if entry_lev > 2:
                mid_layout = QHBoxLayout()
                #left_layout = QVBoxLayout()
                                             
                form = QFormLayout()
                form.setContentsMargins(0,0,-1,-1)
            
                self.withinpix_homo = QCheckBox()
                self.withinpix_homo_lab = QLabel("Include WITHIN Pix homogeneity?") 
                form.addRow(self.withinpix_homo_lab, self.withinpix_homo)  
                self.withinpix_homo_lab.setFont(QFont("Times",weight=QFont.Bold))
                if entry_lev >= 4:
                    self.withinpix_homo.setCheckState(Qt.Checked)
                else:
                    self.withinpix_homo.setCheckState(Qt.Unchecked)
                self.withinpix_homo.stateChanged.connect(self.include_exclude_withinpix_info)
            
                self.purepix = QCheckBox()
                form.addRow(QLabel("Pixel contains single land cover"), self.purepix)            
                self.purepix.setCheckState(0)
                self.purepix.stateChanged.connect(self.populate_pure_percentage)
            
                self.built_entry = QLineEdit()
                form.addRow(QLabel("% BUILT"), self.built_entry)
                self.bare_entry = QLineEdit()
                form.addRow(QLabel("% BARE"), self.bare_entry)
                self.water_entry = QLineEdit()
                form.addRow(QLabel("% WATER"), self.water_entry)
                self.cropmono_entry = QLineEdit()
                form.addRow(QLabel("% MONO CROP LOW"), self.cropmono_entry)
                self.cropmix_entry = QLineEdit()
                form.addRow(QLabel("% MIXED CROP"), self.cropmix_entry)
                self.cropmed_entry = QLineEdit()
                form.addRow(QLabel("% MED CROP"), self.cropmed_entry)
                self.grass_entry = QLineEdit()
                form.addRow(QLabel("% GRASS"), self.grass_entry)
                self.dead_entry = QLineEdit()
                form.addRow(QLabel("% DEAD WOODY"), self.dead_entry)
                self.medveg_entry = QLineEdit()
                form.addRow(QLabel("% MED VEG"), self.medveg_entry)
                self.highveg_entry = QLineEdit()
                form.addRow(QLabel("% TALL WOODY"), self.highveg_entry)
                self.treeplant0_entry = QLineEdit()
                form.addRow(QLabel("% YOUNG TREE PLANT(0-2yrs)"), self.treeplant0_entry)
                self.treeplant_entry = QLineEdit()
                form.addRow(QLabel("% MATURE TREE PLANT"), self.treeplant_entry)
                self.forest_entry= QLineEdit()
                form.addRow(QLabel("% FOREST/TREES"), self.forest_entry)
                self.age_entry=QLineEdit()
                form.addRow(QLabel("Estimated Age"), self.age_entry)
            
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
            
                self.neighborhood_homo = QCheckBox()
                if entry_lev == 5:
                    self.neighborhood_homo.setCheckState(Qt.Checked)
                else:
                    self.neighborhood_homo.setCheckState(Qt.Unchecked)
                self.neighborhood_homo.stateChanged.connect(self.include_exclude_neighborhood_info)
                self.neighborhood_label = QLabel("Include NEIGHBORHOOD homogeneity?",  self.neighborhood_homo)   
                self.neighborhood_label.setFont(QFont("Times",weight=QFont.Bold))
                right_layout.addWidget(self.neighborhood_label)
                right_layout.addWidget(self.neighborhood_homo)
            
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
                self.homonbhd9_label = QLabel("Num neighbors with same LC: (only for center pix)")
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
            
            if entry_lev > 2:
                self.stability_entry = QComboBox()
                self.stability_entry.addItems(["--","c - true change", "s - stable", "of - seasonal fluc.", 
                                     "rf - regular fluc. (tides)", "pi - positional instability"])
                main_layout_foot.addRow(QLabel("stability note"), self.stability_entry)
                self.state_entry = QComboBox()
                self.state_entry.addItems(["--","Bare","Young","Mature","Harvest","Burnt","Flooded","Fallowed","Deciduous-partial","Deciduous-full"])
                main_layout_foot.addRow(QLabel("current state"), self.state_entry)
                
            self.notes_entry = QLineEdit()
            main_layout_foot.addRow(QLabel("Notes"), self.notes_entry)
            main_layout.addLayout(main_layout_foot)
            
            self.model = QSqlRelationalTableModel(db=db)
            self.model.setTable('PixelVerification')
                                                  
            ## setting up relations with LC5 and LC tables so that text is seen but ints are stored
            lc5_col = self.model.fieldIndex('LC5') # column of main table in which LC5 variable is stored
            self.model.setRelation(lc5_col, QSqlRelation('LC5','LC5id','LC5type')) # (table, id to store, value to show)
            self.lc_gen_relmodel = self.model.relationModel(lc5_col)
            self.lc_gen_picker.setModel(self.lc_gen_relmodel)
            self.lc_gen_picker.setModelColumn(self.lc_gen_relmodel.fieldIndex('LC5type'))
            self.lc_gen_picker.activated.connect(self.update_lc_choices) 
                    
            lc_col = self.model.fieldIndex('LC') # column of main table in which LC variable is stored 
            if entry_lev == 1:
                self.model.setRelation(lc_col, QSqlRelation('LC_simp','LC_UNQ','USE_NAME'))  # (table, id to store, value to show)
            else:   
                self.model.setRelation(lc_col, QSqlRelation('LC','LC_UNQ','USE_NAME'))  # (table, id to store, value to show)
            self.lc_detail_relmodel = self.model.relationModel(lc_col)
            self.lc_detail_picker.setModel(self.lc_detail_relmodel)
            self.lc_detail_picker.setModelColumn(self.lc_detail_relmodel.fieldIndex('USE_NAME'))   
            self.lc_detail_picker.activated.connect(self.update_lc5_choices)
                  
            #self.model.setEditStrategy(QSqlRelationalTableModel.OnManualSubmit)
            self.mapper = QDataWidgetMapper()
            self.mapper.setModel(self.model)
            # ItemDelegate needs to be set to save selections in Comboboxes (as they are populated with relational models)
            self.mapper.setItemDelegate(QSqlRelationalDelegate())
            self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
            
            self.mapper.addMapping(self.recid_info, 0)
            self.mapper.addMapping(self.pid_info, 1)
            #self.mapper.addMapping(self.pid0_entry, 2)
            #self.mapper.addMapping(self.pid1_entry, 3)
            self.mapper.addMapping(self.imgdate_entry, 4)
            
            self.mapper.addMapping(self.lc_gen_picker, lc5_col)
            self.mapper.addMapping(self.lc_detail_picker, lc_col)
            
            if entry_lev > 2:   
                self.mapper.addMapping(self.forestprox_entry, 8)
                self.mapper.addMapping(self.waterprox_entry, 9)
                self.mapper.addMapping(self.percenttree_entry, 10)
                
                self.mapper.addMapping(self.homonbhd9_entry, 7)                                      
                self.mapper.addMapping(self.built_entry, 11)
                self.mapper.addMapping(self.bare_entry, 12)
                self.mapper.addMapping(self.water_entry, 13)
                self.mapper.addMapping(self.cropmono_entry, 14)
                self.mapper.addMapping(self.cropmix_entry, 15)
                self.mapper.addMapping(self.cropmed_entry, 16)
                self.mapper.addMapping(self.grass_entry, 17)
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
            self.mapper.addMapping(self.entry_lev_info, 28)
            
            self.model.select()
            ## Add the following two lines to allow form to view past record 255
            ##  TODO: implement partial reads to avoid reading full db for everything?
            while self.model.canFetchMore():
                self.model.fetchMore()
            self.mapper.toLast()
           
            self.setMinimumSize(QSize(250, 600))
            
            controls = QHBoxLayout()
  
            prev_rec = QPushButton("<rec")
            prev_rec.clicked.connect(self.get_prev_rec)
            next_rec = QPushButton(">rec")
            next_rec.clicked.connect(self.get_next_rec)
            next_pix = QPushButton(">>pix")
            next_pix.clicked.connect(self.get_next_pix)
            next_pix_c = QPushButton(">pix")
            next_pix_c.clicked.connect(self.get_next_pix_consec)
            save_rec = QPushButton("Save Changes")
            save_rec.clicked.connect(self.update_record)
            controls.addWidget(prev_rec)
            controls.addWidget(next_rec)
            controls.addWidget(next_pix_c)
            controls.addWidget(next_pix)
            controls.addWidget(save_rec)
            
            #layout.addLayout(form)
            main_layout.addLayout(controls)
            
            widget = QWidget()
            widget.setLayout(main_layout)
            self.setCentralWidget(widget)

            self.color_neighborhood()
            
            
        #def initializeUI(self):
        def reset_filters(self):
            self.lc_detail_relmodel.setFilter("")
            self.lc_gen_relmodel.setFilter("")
            
        def get_next_rec(self):
            self.reset_filters()
            while self.model.canFetchMore():
                self.model.fetchMore()
            self.mapper.toNext()
            
        def get_prev_rec(self):
            self.reset_filters()
            self.mapper.toPrevious()
            
        def validate_date(self):
            passing = True
            date_entry = self.imgdate_entry.text()
            #print('checking date entry: {}'.format(date_entry))
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
                #print('formatting ok')
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
            if entry_lev > 2:
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
            add_fields = QSqlQuery("UPDATE PixelVerification SET PID0=?, PID1=? WHERE recID=?")
            add_fields.bindValue(2, this_rec_id)
            add_fields.bindValue(0, self.pid_info.text().split('_')[0])
            add_fields.bindValue(1, self.pid_info.text().split('_')[1])
            qry_stat = add_fields.exec()
            if qry_stat is not True:
                errorText = add_fields.lastError().text()
                QMessageBox.critical(self, 'Error getting new pid0 or pid1:', errorText)
            self.mapper.submit()
        
        def new_pid(self,pid,dt=None):
            if '_' in pid:
                pidx = pid
                pid0 = pid.split('_')[0]
                pid1 = pid.split('_')[1]
            else:
                pid0 = pid
                pid1 = 0
                pidx = f'{pid0}_0'

                add_query = QSqlQuery()
                
                if dt: 
                    add_query.prepare("INSERT INTO PixelVerification (PID, PID0, PID1, LC5, LC, entry_lev, imgDate)"
                          "VALUES( ?, ?, ?, ?, ?, ?, ?)")
                    add_query.bindValue(6, dt)
                else:
                    add_query.prepare("INSERT INTO PixelVerification (PID, PID0, PID1, LC5, LC, entry_lev)"
                          "VALUES( ?, ?, ?, ?, ?, ?)")
                    
                add_query.bindValue(0, pidx)
                add_query.bindValue(1, pid0)
                add_query.bindValue(2, pid1)
                add_query.bindValue(3, 0)
                add_query.bindValue(4, 0)
                add_query.bindValue(5, entry_lev)
                add_query.exec()
                self.mapper.submit()
                self.model.select() 
                while self.model.canFetchMore():
                    self.model.fetchMore()
                self.mapper.toLast()
                self.color_neighborhood()
        
        def add_pid(self):
            '''
            To implement add_pid directly via button
            '''
            # pid can either be entered as single number(pid0) or as full pid(pid0_pid1)
            text, ok = QInputDialog().getText(self, "PID chooser",
                                     "PID:", QLineEdit.Normal)
            if ok and text:
                ## mapke sure that pid being entered fits formatting criteria:
                if text.isdigit() or (text.split('_')[0].isdigit() and text.split('_')[1].isdigit()):  
                    self.new_pid(text)
                else:
                    msg = QMessageBox()
                    msg.setWindowTitle("INCORRECT FORMAT")
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("pid format needs to be number or number_number")
                    msg.exec_()
        
        def get_row_of_record(self, rec_match):
            rec = self.model.fieldIndex('recID') 
            for row in range (self.model.rowCount()):
                data = self.model.data(self.model.createIndex(row,rec))
                if data == rec_match:
                    return row
            return -1

        def goto_record(self,pid,dt=None):
            #print(pid)
            # pid is a string, either entered as a single number(pid0) or as full pid(pid0_pid1)
            if dt:
                pid_qry = QSqlQuery("SELECT rowid, recID from PixelVerification where PID = ? AND imgDate=?")
                pid_qry.bindValue(1, dt)
            else:
                pid_qry = QSqlQuery("SELECT rowid, recID from PixelVerification where PID = ?")
                
            if '_' in pid:
                pid_qry.bindValue(0, pid)
            else:
                pid0 = pid
                pid_qry.bindValue(0, f'{pid0}_0')
                
            pid_qry.exec()
            pidmodel = QSqlQueryModel(self)
            pidmodel.setQuery(pid_qry)
            rec = pidmodel.record(0).value(1)
            row = self.get_row_of_record(rec)  # note this seems like an inefficient way to get the row #...

            if rec==None: 
                buttonReply = QMessageBox.question(
                    self, "RECORD DOES NOT EXIST", "Do you want to create new record?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

                #buttonReply.setIcon(QMessageBox.Warning)  #cannot set icon on standatd button object
                
                if buttonReply == QMessageBox.Yes:
                    self.new_pid(pid,dt)
                    return True
                else:
                    return False
            
            else:
                #print(f'going to rec:{rec}')
                #pid_qry.seek(rec)  # not working...
                self.mapper.submit()
                self.model.select()
                while self.model.canFetchMore():
                    self.model.fetchMore() 
                self.mapper.setCurrentIndex(row)
                self.color_neighborhood()
                
        def goto_pid(self):
            '''
            To implement goto_record directly via button
            '''
            # pid can either be entered as single number(pid0) or as full pid(pid0_pid1)
            text, ok = QInputDialog().getText(self, "PID chooser",
                                     "PID:", QLineEdit.Normal)
            if ok and text:
                self.goto_record(text)  
                      
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
                this_lc5 = self.lc_gen_picker.currentText()
                #print('lc5:{}'.format(this_lc5))
                
                if this_pid =='' or this_lc=='' or this_lc5==0:
                    msg = QMessageBox()
                    msg.setWindowTitle("MISSING DATA")
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("need to fill all yellow fields")
                    msg.exec_()
                
                    return False
            
                elif entry_lev > 2 and self.withinpix_homo.isChecked() == True:
                    ## Check if Land cover %s sum to 100:
                    per_built = self.built_entry.text()
                    per_bare = self.bare_entry.text()
                    per_water = self.water_entry.text()
                    per_cropm = self.cropmono_entry.text()
                    per_cropmix = self.cropmix_entry.text()
                    per_cropmed = self.cropmed_entry.text()
                    per_grass = self.grass_entry.text()
                    per_dead = self.dead_entry.text()
                    per_medveg = self.medveg_entry.text()
                    per_treeplant0 = self.treeplant0_entry.text()
                    per_highveg = self.highveg_entry.text()
                    per_treeplant = self.treeplant_entry.text()
                    per_forest = self.forest_entry.text()
                
                    lcs = [per_built,  per_bare, per_water, per_cropm, per_cropmix, per_cropmed, per_grass, 
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
                else:
                    return True
        
        @QtCore.pyqtSlot(int)

        def include_exclude_withinpix_info(self):
            if self.withinpix_homo.isChecked() == False:
                print(f'within pix info is not required')
        
        def include_exclude_neighborhood_info(self):
            if self.neighborhood_homo.isChecked() == False:
                print(f'neighborhood info is not required')
        
        def update_lc_selection(self):
            ## Not working
            self.lc_detail_picker.blockSignals(True)
            self.lc_detail_relmodel.setFilter("")
            self.lc_detail_picker.blockSignals(False)
            #self.lc_detail_picker.setCurrentIndex(0)
            
        def update_lc_choices(self, i):
            self.lc_detail_relmodel.setFilter ("LC5_name like'" +self.lc_gen_picker.itemText(i)+ "%%'")
            
        def update_lc5_choices(self, i):
            lc = self.lc_detail_picker.itemText(i)
            lc = str(self.lc_detail_picker.currentText())
            lc5_qry = QSqlQuery()
            lc5_qry.prepare("SELECT USE_NAME, LC5_name from LC WHERE USE_NAME=?")
            lc5_qry.bindValue(0,lc)
            lc5_qry.exec()
            lc5_qry.next()
            lc5 = lc5_qry.value(1)
            self.lc_gen_relmodel.setFilter("LC5type like'" +lc5+ "%%'")
        
        def get_next_recid(self):
            id_qry = QSqlQuery("SELECT MAX(recID) FROM PixelVerification") 
            id_qry.exec()
            id_qry.next()
            next_rec = id_qry.value(0) + 1
            
            return next_rec
        
        def populate_pure_percentage(self):
            '''
            enter 100 in corresponding field if pixel is marked as pure
            '''
            if entry_lev > 2 and self.purepix.isChecked() == True:
                lc = str(self.lc_detail_picker.currentText())
                if lc == 'NoVeg_Bare':
                    self.bare_entry.setText('100')
                elif lc == 'NoVeg_Built':
                    self.built_entry.setText('100')
                elif lc == 'NoVeg_Water':
                    self.water_entry.setText('100')
                elif lc.startswith('Grass'):
                    self.grass_entry.setText('100')
                elif lc.startswith('Crops-Orchard') or lc in ['Crops-Banana','Crops-Yerba-Mate','Crops-Vineyard','D_Crop_Med']:
                    self.cropmed_entry.setText('100')
                elif lc == 'M_Crops-mix':
                    self.cropmix_entry.setText('100')
                elif lc.startswith('Crop') or lc == 'L_Crop-Low':    
                    self.cropmono_entry.setText('100')
                elif lc == 'TreePlant-new':
                    self.treeplant0_entry.setText('100')
                elif lc.startswith('TreePlant'):
                    self.treeplant_entry.setText('100')
                elif lc.startswith('Tree'):
                    self.forest_entry.setText('100')
                elif lc in ['Cleared','Burnt-woody']:
                    self.dead_entry.setText('100')
                elif lc in ['Shrub','Grass_tree-mix']:
                    self.medveg_entry.setText('100')
                elif lc == 'HighVeg':
                    self.highveg_entry.setText('100')
             
        def get_next_pix(self):
            '''
            starts new record after next available pixel number (greatest existing pixel id + 1) -- skips any gaps
            '''
            ## Perform data checks and save current row
            self.update_record()
            if self.check_data() == False:
                return False    
            else:
                if self.neighborhood_homo.isChecked() == True:
                    self.get_neighborhood_info
                    if len(self.changed_neighbors) < 9:
                        print(len(self.changed_neighbors))
                        msg = QMessageBox()
                        msg.setWindowTitle("MISSING NEIGHBORS")
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("click on cells that are different or submit neighborhood (to copy/paste)")
                        msg.exec_()
                        return False
                
            id_query = QSqlQuery()
            id_query.prepare("SELECT recID, MAX(PID0) FROM PixelVerification")
            id_query.exec()
            if id_query.next() is None:
                pid0 = 1
            else:
                #print(f'max pixel value is: {id_query.value(1)}')
                pid0 = id_query.value(1) + 1
            pid = f"{pid0}_0"
            add_query = QSqlQuery()
            add_query.prepare("INSERT INTO PixelVerification (PID, PID0, PID1, LC5, LC, entry_lev)"
                          "VALUES( ?, ?, ?, ?, ?, ?)")
            add_query.bindValue(0, pid)
            add_query.bindValue(1, pid0)
            add_query.bindValue(2, 0)
            add_query.bindValue(3, 0)
            add_query.bindValue(4, 0)
            add_query.bindValue(5, entry_lev)
            add_query.exec()
            self.mapper.submit()
            self.model.select() 
            self.reset_filters()
            while self.model.canFetchMore():
                self.model.fetchMore()
            self.mapper.toLast()
            self.color_neighborhood()
                        
            return True
        
        def get_next_pix_consec(self):
            '''
            starts new record at next pixel number in sequence that does not have existing record
            '''
            ## Perform data checks and save current row
            self.update_record()
            if self.check_data() == False:
                return False   
            else:
                if entry_lev > 2 and self.neighborhood_homo.isChecked() == True:
                    self.get_neighborhood_info
                    if len(self.changed_neighbors) < 9:
                        print(len(self.changed_neighbors))
                        msg = QMessageBox()
                        msg.setWindowTitle("MISSING NEIGHBORS")
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("click on cells that are different or submit neighborhood (to copy/paste)")
                        msg.exec_() 
                        return False
                
            found_next = False
            this_pid = self.pid_info.text()
            this_pid0 = this_pid.split('_')[0]
            i = int(this_pid0)
            while found_next == False:
                i = i+1
                id_query = QSqlQuery()
                id_query.prepare("SELECT recID, PID0 FROM PixelVerification WHERE PID0=?")
                id_query.bindValue(0,i)
                id_query.exec()
                if id_query.next():
                    found_next = False
                else:
                    found_next = True
                    pid = f"{i}_0"
                    add_query = QSqlQuery()
                    add_query.prepare("INSERT INTO PixelVerification (PID, PID0, PID1, LC5, LC, entry_lev)"
                          "VALUES( ?, ?, ?, ?, ?, ?)")
                    add_query.bindValue(0, pid)
                    add_query.bindValue(1, i)
                    add_query.bindValue(2, 0)
                    add_query.bindValue(3, 0)
                    add_query.bindValue(4, 0)
                    add_query.bindValue(5, entry_lev)
                    add_query.exec()
                    self.mapper.submit()
                    self.model.select() 
                    self.reset_filters()
                    while self.model.canFetchMore():
                        self.model.fetchMore()
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
                    ## Will copy all neighbors that have data entered for this date
                    ## TODO add method to edit all neighbors together after copying
                    this_rec_id = self.recid_info.text()
                    this_pid = self.pid_info.text()
                    this_date = self.imgdate_entry.text()
                    next_rec = self.get_next_recid() 
                    print(f'next record id = {next_rec}')
                    
                    pid0 = this_pid.split('_')[0]
                    for i in range(9):
                        pid = f'{pid0}_{i}'
                        next_recid = (next_rec+i)
                        cpy_qry = QSqlQuery("CREATE TABLE tempTable AS SELECT * FROM PixelVerification WHERE PID=? AND imgDate=?")
                        cpy_qry.bindValue(0,pid)
                        cpy_qry.bindValue(1,this_date)
                        cpy_qry.exec()
                        fix_cpy_qry = QSqlQuery("UPDATE tempTable SET recID=?, imgDate=?")
                        fix_cpy_qry.bindValue(0,(next_recid))
                        fix_cpy_qry.bindValue(1,entry)
                        fix_cpy_qry.exec()
                        ## Paste record into pixel verificaiton table
                        QSqlQuery("INSERT INTO PixelVerification SELECT * FROM tempTable").exec()
                        QSqlQuery("DROP TABLE tempTable").exec()
      
                    self.mapper.submit()
                    self.model.select()
                    while self.model.canFetchMore():
                        self.model.fetchMore()
                    self.mapper.toLast()
                    self.color_neighborhood()
                
                    ## If it did not succeed (there is no new record), probably because there are duplicate dates
                    ##    (this works because we get two records with the same recID and cannot insert them)
                    ##    warn user so they do not modify previous record
                    if self.recid_info.text() == next_rec:
                        msg = QMessageBox()
                        msg.setWindowTitle("DID NOT ADD RECORD")
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("check for duplicate dates")
                        msg.exec_()
                    
                        return False
                    else:
                        return True
                
                
        def add_neighbor(self):
            ## check if record already exists and go to it if it does
            this_neighbor = int(self.sender().objectName().split('_')[1])
            #print(this_neighbor)
            this_rec_id = self.recid_info.text()
            this_pid = self.pid_info.text()
            this_pid0 = this_pid.split('_')[0]
            next_rec = self.get_next_recid() 
            this_date = self.imgdate_entry.text()
            new_pid = f'{this_pid0}_{this_neighbor}'
            #print(new_pid)
            check_qry = QSqlQuery("SELECT * FROM PixelVerification WHERE PID=? AND imgDate=?")
            check_qry.bindValue(0,new_pid)
            check_qry.bindValue(1,this_date)
            check_qry.exec()
            if check_qry.next():
                msg = QMessageBox()
                msg.setWindowTitle("DUPLICATE RECORD")
                msg.setIcon(QMessageBox.Warning)
                msg.setText("There is already a record in the db for this PID and date")
                ret = msg.question(self,'', "Do you want to go to the existing record?", msg.Yes | msg.No)
                
                if ret == msg.Yes:
                    self.goto_record(new_pid,this_date)
                    return True
                
                else:
                    return False
            else:
                self.mapper.submit()
                data_clean = self.check_data()
                if data_clean == False:
                    return False
                    
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    ret = msg.question(self,'', "Do you want to go to edit this neighbor?", msg.Yes | msg.No)

                    if ret == msg.Yes:

                        print(f'copying record for neighbor {this_neighbor}')
                        cpy_qry = QSqlQuery("CREATE TABLE tempTable AS SELECT * FROM PixelVerification WHERE PID=? AND imgDate=?")
                        cpy_qry.bindValue(0,this_pid)
                        cpy_qry.bindValue(1,this_date)
                        cpy_qry.exec()
                
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
                        while self.model.canFetchMore():
                            self.model.fetchMore()
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
                    else:
                        return False
    
        def submit_neighborhood(self):
            
            data_clean = self.check_data()
            if data_clean == False:
                return False
            
            else:
                this_pid = self.pid_info.text()
                this_pid0 = self.pid_info.text().split('_')[0]
                cent_pid = f'{this_pid0}_0'
                
                next_rec = self.get_next_recid()
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
                    print('adding neighborhood pixels...')
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