#!python
# Copyright (c) 2015, Sven Thiele <sthiele78@gmail.com>
#
# This file is part of meneco-gui.
#
# meneco-gui is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# meneco-gui is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with meneco-gui.  If not, see <http://www.gnu.org/licenses/>.
# -*- coding: utf-8 -*-
import sys, time
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from pyasp.asp import *
from __meneco__ import query, utils, sbml

class CompletionThread(QThread):
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        self.wid=parent
 
    def print_met(self,predictions) :
      for p in predictions: 
        if p.pred() == "xreaction" : self.emit(SIGNAL("asignal"),'  '+str(p.arg(0)))
        if p.pred() == "unproducible_target" : self.emit(SIGNAL("asignal"),'  '+str(p.arg(0)))
 
    def run(self):

        self.emit(SIGNAL("asignal"),'\nChecking draftnet for unproducible targets ...')    

        model = query.get_unproducible(self.wid.draftnet, self.wid.targets, self.wid.seeds)
        self.emit(SIGNAL("asignal"),'done.')
        self.emit(SIGNAL("asignal"),' '+str(len(model))+' unproducible targets:')
        self.print_met(model.to_list())
        unproducible_targets = TermSet()
        for a in model :
          target= str(a)[13:]
          t = String2TermSet(target)
          unproducible_targets = unproducible_targets.union(t)
        
        
        if(self.wid.repairnet != 0):
          all_reactions = self.wid.draftnet
          all_reactions = all_reactions.union(self.wid.repairnet)
          self.emit(SIGNAL("asignal"),'\nChecking draftnet + repairnet for unproducible targets ...')
          model = query.get_unproducible(all_reactions, self.wid.seeds, self.wid.targets)
          self.emit(SIGNAL("asignal"),'done.')
          self.emit(SIGNAL("asignal"),'  still '+str(len(model))+' unproducible targets:')
          self.print_met(model.to_list())
          never_producible = TermSet()
          for a in model :
            target= str(a)[13:]
            t = String2TermSet(target)
            never_producible = never_producible.union(t)

          reconstructable_targets = TermSet()
          for t in unproducible_targets:
            if not (t in never_producible) :      reconstructable_targets.add(t)
          self.emit(SIGNAL("asignal"),'\n '+str(len(reconstructable_targets))+' targets to reconstruct:')
          self.print_met(reconstructable_targets)   
          
          if len(reconstructable_targets)== 0 : 
            utils.clean_up()
            self.emit(SIGNAL("finishedsignal"),False)
            return
     
    
          essential_reactions = TermSet()
          for t in reconstructable_targets:
            single_target = TermSet()
            single_target.add(t)
            self.emit(SIGNAL("asignal"),'\nComputing essential reactions for '+str(t)+' ...')
            essentials =  query.get_intersection_of_completions(self.wid.draftnet, self.wid.repairnet, self.wid.seeds, single_target)
            self.emit(SIGNAL("asignal"),'done.')
            self.emit(SIGNAL("asignal"),' '+str(len(essentials))+' essential reactions found:')
            self.print_met(essentials.to_list())
            essential_reactions = essential_reactions.union(essentials)
          self.emit(SIGNAL("asignal"),'\n  Overall '+str(len(essential_reactions))+' essential reactions found.')
          self.print_met(essential_reactions)
          self.emit(SIGNAL("asignal"),'\n Add essential reactions to network.')
          ndraftnet  = essential_reactions.union(self.wid.draftnet) 

          utils.clean_up()
          
          self.emit(SIGNAL("asignal"),'\nComputing one minimal completion to produce all targets ...')
          optimum, models =  query.get_minimal_completion_size(ndraftnet, self.wid.repairnet, self.wid.seeds, reconstructable_targets)
          self.emit(SIGNAL("asignal"),'done.')
          self.emit(SIGNAL("asignal"),'  minimal size = '+str(optimum[0]))
          self.print_met(models[0].to_list())
          
          self.emit(SIGNAL("asignal"),'\nComputing common reactions in all completion with size '+str(optimum[0])+' ...')
          model =  query.get_intersection_of_optimal_completions(ndraftnet, self.wid.repairnet, self.wid.seeds, reconstructable_targets,  optimum[0])
          self.emit(SIGNAL("asignal"),'done.')
          self.print_met(model.to_list())
          
          self.emit(SIGNAL("asignal"),'\nComputing union of reactions from all completion with size '+str(optimum[0])+' ...')
          model =  query.get_union_of_optimal_completions(ndraftnet,  self.wid.repairnet,  self.wid.seeds, reconstructable_targets, optimum[0])
          self.emit(SIGNAL("asignal"),'done.')
          self.print_met(model.to_list())
          
          #do_repair= raw_input('\nDo you want to compute all completions with size '+str(optimum[0])+' Y/n:')
          #if wid.do_repair:
            #self.emit(SIGNAL("asignal"),'\nComputing all completions with size '+str(optimum[0])+' ...')
            #models =  query.get_optimal_completions(ndraftnet, self.wid.repairnet, self.wid.seeds, reconstructable_targets, optimum[0])
            #self.emit(SIGNAL("asignal"),'done.')
            #count = 1
            #for model in models:
              #self.emit(SIGNAL("asignal"),'Completion '+str(count)+':')
              #count+=1
              #self.print_met(model.to_list())
      
        utils.clean_up()
        self.emit(SIGNAL("finishedsignal"),False)    

class MenecoGui(QWidget):
    
    def __init__(self):
        super(MenecoGui, self).__init__()
        self.draftnet = 0
        self.seeds = 0
        self.targets = 0
        self.repairnet = 0
        self.initUI()
        
    def checkState(self):
      palette = QPalette()
      palette.setColor(QPalette.Foreground,Qt.green)
      if(self.draftnet != 0): 
        self.lbl1.setText(u'\u2714')
        self.lbl1.setPalette(palette)
      if(self.seeds != 0): 
        self.lbl2.setText(u'\u2714')
        self.lbl2.setPalette(palette)
      if(self.targets != 0): 
        self.lbl3.setText(u'\u2714')
        self.lbl3.setPalette(palette)
      if(self.repairnet != 0):
        self.lbl4.setText(u'\u2714')
        self.lbl4.setPalette(palette)         
      
      if(self.draftnet != 0 and self.seeds != 0 and self.targets != 0):
        self.btn5.setEnabled(True)
      else: self.btn5.setEnabled(False)
      if(self.draftnet != 0 and self.seeds != 0 and self.targets != 0 and self.repairnet != 0):
        self.btn6.setEnabled(True)
      else: self.btn6.setEnabled(False)
      return                
        
    def print_met(self,predictions) :
      for p in predictions: 
        if p.pred() == "xreaction" : self.textBox.append('  '+str(p.arg(0)))
        if p.pred() == "unproducible_target" : self.textBox.append('  '+str(p.arg(0)))
        
    def checkproducebilty(self):
        self.set_busy(True)
        self.textBox.append('\nChecking draftnet for unproducible targets ...')
        model = query.get_unproducible(self.draftnet, self.targets, self.seeds)
        self.textBox.append('done.')
        self.textBox.append(' '+str(len(model))+' unproducible targets:')
        self.print_met(model.to_list())
        unproducible_targets = TermSet()
        for a in model :
          target= str(a)[13:]
          t = String2TermSet(target)
          unproducible_targets = unproducible_targets.union(t)
        
        if(self.repairnet != 0):
          all_reactions = self.draftnet
          all_reactions = all_reactions.union(self.repairnet)
          self.textBox.append('\nChecking draftnet + repairnet for unproducible targets ...')
          model = query.get_unproducible(all_reactions, self.seeds, self.targets)
          self.textBox.append('done.')
          self.textBox.append('  still '+str(len(model))+' unproducible targets:')
          self.print_met(model.to_list())
          never_producible = TermSet()
          for a in model :
            target= str(a)[13:]
            #print target
            t = String2TermSet(target)
            never_producible = never_producible.union(t)

          reconstructable_targets = TermSet()
          for t in unproducible_targets:
            if not (t in never_producible) :      reconstructable_targets.add(t)
          self.textBox.append('\n '+str(len(reconstructable_targets))+' targets to reconstruct:')
          self.print_met(reconstructable_targets)
      
        utils.clean_up()
        self.set_busy(False)
        self.checkState()
        return           
        
        
    def set_busy(self,busy):
      if busy:
        self.btn1.setEnabled(False)
        self.btn2.setEnabled(False)
        self.btn3.setEnabled(False)
        self.btn4.setEnabled(False)
        self.btn5.setEnabled(False)
        self.btn6.setEnabled(False)
      else:
        self.btn1.setEnabled(True)
        self.btn2.setEnabled(True)
        self.btn3.setEnabled(True)
        self.btn4.setEnabled(True)
        self.btn5.setEnabled(True)
        self.btn6.setEnabled(True)
        
    def complete(self):
        self.set_busy(True)
        self.completionthread.start()
        return    
        
    def completion_finished(self):
        self.set_busy(False)
        self.checkState()
        return 
        
        
    def addText(self,msg):        
        self.textBox.append(msg)
        return   
        
    def initUI(self):  
    
        self.completionthread = CompletionThread(self)
        
        QObject.connect(self.completionthread,SIGNAL("asignal"),self.addText)
        QObject.connect(self.completionthread,SIGNAL("finishedsignal"),self.completion_finished)
        
        self.btn1 = QPushButton('Load draft network')
        #btn1.setToolTip('This is a <b>QPushButton</b> widget')
        self.btn1.clicked.connect(self.loadDraftDialog)   
        
        self.btn2 = QPushButton('Load seeds')
        #btn2.setToolTip('This is a <b>QPushButton</b> widget')
        self.btn2.clicked.connect(self.loadSeedsDialog)    
        
        self.btn3 = QPushButton('Load targets')
        #btn3.setToolTip('This is a <b>QPushButton</b> widget')
        self.btn3.clicked.connect(self.loadTargetsDialog)    
        
        self.btn4 = QPushButton('Load Repair DB')
        #btn4.setToolTip('This is a <b>QPushButton</b> widget')
        self.btn4.clicked.connect(self.loadRepairDBDialog)  
        
        
        self.lbl1 = QLabel("UNKNOWN")
        self.lbl2 = QLabel("UNKNOWN")
        self.lbl3 = QLabel("UNKNOWN")
        self.lbl4 = QLabel("UNKNOWN")
                
        palette = QPalette()
        palette.setColor(QPalette.Foreground,Qt.red)
        self.lbl1.setPalette(palette)
        self.lbl2.setPalette(palette)
        self.lbl3.setPalette(palette)
        self.lbl4.setPalette(palette)
        
        
        self.btn5 = QPushButton('Check Producebility')
        #btn1.setToolTip('This is a <b>QPushButton</b> widget')
        self.btn5.clicked.connect(self.checkproducebilty)    
        self.btn5.setEnabled(False)
        
        self.btn6 = QPushButton('Complete Network')
        #btn2.setToolTip('This is a <b>QPushButton</b> widget')
        self.btn6.clicked.connect(self.complete)
        self.btn6.setEnabled(False)
        
        self.textBox = QTextEdit()
        self.textBox.setReadOnly(True)
       
        vbox = QVBoxLayout(self)
        hbox = QHBoxLayout()
        hbox2 = QHBoxLayout()
        
        topleft = QVBoxLayout()        
        topmleft = QVBoxLayout()        
        topmright = QVBoxLayout()        
        topright = QVBoxLayout()
            
        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)
        vbox.addWidget(self.textBox)
        
        hbox.addLayout(topleft)
        hbox.addLayout(topmleft)
        hbox.addLayout(topmright)
        hbox.addLayout(topright) 
        
        topleft.addWidget(self.btn1)
        topleft.addWidget(self.lbl1)
        topmleft.addWidget(self.btn2)
        topmleft.addWidget(self.lbl2)
        topmright.addWidget(self.btn3)
        topmright.addWidget(self.lbl3)
        topright.addWidget(self.btn4)
        topright.addWidget(self.lbl4)
        
        hbox2.addWidget(self.btn5)
        hbox2.addWidget(self.btn6)

        self.setLayout(vbox)

        
        self.setGeometry(600, 600, 600, 500)
        self.setWindowTitle('Meneco Gui')    
        self.show()
        
        
    def loadDraftDialog(self):
        self.set_busy(True)
        fname = QFileDialog.getOpenFileName(self, 'Open draft file')
        if os.path.isfile(fname) :
          self.textBox.append('Reading draft network from '+fname+'...')        
          #self.draftnet = sbml.read_draftnetworkSBML(fname)
          try:
            self.draftnet = sbml.readSBMLnetwork(fname, 'draft')
            self.textBox.append('done.') 
          except:  self.textBox.append('failed.')    
        self.set_busy(False)            
        self.checkState()

            
    def loadRepairDBDialog(self):
        self.set_busy(True)
        fname = QFileDialog.getOpenFileName(self, 'Open repair file')
        if os.path.isfile(fname) :
          self.textBox.append('Reading repair network from '+fname+'...')        
          try:
            self.repairnet = sbml.readSBMLnetwork(fname, 'repairnet')
            self.textBox.append('done.')  
          except:  self.textBox.append('failed.')     
        self.set_busy(False) 
        self.checkState()
        
 
    def loadSeedsDialog(self):
        self.set_busy(True)
        fname = QFileDialog.getOpenFileName(self, 'Open seeds file')
        if os.path.isfile(fname) :
          self.textBox.append('Reading seeds from '+fname+'...')        
          try:
            self.seeds = sbml.readSBMLseeds(fname)
            self.textBox.append('done.')
          except: self.textBox.append('failed.') 
        self.set_busy(False) 
        self.checkState()
          
    def loadTargetsDialog(self):
        self.set_busy(True)
        fname = QFileDialog.getOpenFileName(self, 'Open target file')
        if os.path.isfile(fname) :
          self.textBox.append('Reading targets from '+fname+'...')        
          try:
            self.targets = sbml.readSBMLtargets(fname)
            self.textBox.append('done.') 
          except: self.textBox.append('failed.') 
        self.set_busy(False)
        self.checkState()
        
def main():
    
    app = QApplication(sys.argv)
    myGui = MenecoGui()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()    
