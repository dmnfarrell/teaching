#!/usr/bin/env python

"""
    Toytree viewer.
    Created Jan 2021
    Copyright (C) Damien Farrell

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import sys, os, io
import numpy as np
import string
try:
    from PySide2 import QtCore
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import QObject, Signal, Slot
except:
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import *
    from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
import toytree, toyplot

class TreeViewer(QMainWindow):
    """Phylogeny viewer with toytree"""
    def __init__(self):

        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Toytree-viewer")
        self.setGeometry(QtCore.QRect(200, 200, 800, 600))
        self.setMinimumHeight(150)
        self.main = QWidget(self)
        self.main.setFocus()
        self.setCentralWidget(self.main)
        self.add_widgets()
        self.create_menu(self)
        self.tree = None
        self.width = 400
        self.height = 500

        self.colors = {}
        self.default_style = {
            "layout":'r',
            "edge_type": 'p',
            "edge_style": {
                "stroke": 'black',
                "stroke-width": 2,
            },
            "tip_labels": True,
            "tip_labels_align": True,
            "tip_labels_colors": 'black',
            "tip_labels_style": {
                "font-size": "14px"
            },
            "node_labels": False,
            "node_sizes": 10,
            "node_colors": toytree.colors[2],
            "node_markers":"c",
            "use_edge_lengths":True,
        }
        self.style = self.default_style.copy()
        #self.test_tree(10)
        return

    def test_tree(self, n=None):
        """Load a test tree"""

        if n==None:
            n, ok = QInputDialog().getInt(self, "Test tree",
                                                 "Nodes:", 10)
            if not ok:
                return
        self.set_tree(self.random_tree(n=n))
        self.height = 200+self.tree.ntips*10
        self.update()
        return

    def random_tree(self, n=12):
        """Make a random tree"""

        tre = toytree.rtree.coaltree(n)
        ## assign random edge lengths and supports to each node
        for node in tre.treenode.traverse():
            node.dist = np.random.exponential(1)
            node.support = int(np.random.uniform(50, 100))
        return tre

    def save_data(self):
        """Save layers"""

        data = tools.get_attributes(self)
        data['tree'] = self.tree
        return data

    def load_data(self, data):
        """Load saved layers"""

        try:
            self.set_tree(data['tree'])
            tools.set_attributes(self, data)
        except:
            pass
        self.update()
        return

    def create_menu(self, parent):
        """Menu bar"""

        self.menubar = self.menuBar()
        self.file_menu = QMenu('File', parent)
        self.file_menu.addAction('Import Tree', self.load_tree)
        self.file_menu.addAction('Load Test Tree', self.test_tree)
        self.file_menu.addAction('Export Image', self.export_image)
        self.menubar.addMenu(self.file_menu)
        self.tree_menu = QMenu('Tree', parent)
        self.tree_menu.addAction('Show Unrooted', self.unroot_tree)
        self.tree_menu.addAction('Reset Format', self.reset_style)
        self.menubar.addMenu(self.tree_menu)

        return

    def add_widgets(self):
        """Add widgets"""

        vbox = QVBoxLayout(self.main)
        self.splitter = QSplitter()
        vbox.addWidget(self.splitter)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setSizes([300,100])
        self.splitter.setStretchFactor(1,0)
        #layout.addWidget(self.main)
        from PySide2.QtWebEngineWidgets import QWebEngineView
        self.browser = QWebEngineView()
        self.browser.setMinimumSize(200,200)
        self.splitter.addWidget(self.browser)

        toolswidget = QWidget()
        self.splitter.addWidget(toolswidget)
        l = QVBoxLayout(toolswidget)
        self.zoomslider = w = QSlider(QtCore.Qt.Horizontal)
        w.setSingleStep(5)
        w.setMinimum(5)
        w.setMaximum(50)
        w.setValue(10)
        l.addWidget(w)
        w.valueChanged.connect(self.zoom)
        btn = QPushButton('Set Format')
        l.addWidget(btn)
        btn.clicked.connect(self.tree_style_options)
        t = self.tipitems = QTreeWidget()
        t.setHeaderItem(QTreeWidgetItem(["name","visible"]))
        t.setColumnWidth(0, 200)
        t.setSelectionMode(QAbstractItemView.ExtendedSelection)
        t.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        t.customContextMenuRequested.connect(self.show_tree_menu)
        l.addWidget(t)

        return

    def show_tree_menu(self, pos):
        """Show right cick tree menu"""

        item = self.tipitems.itemAt( pos )
        menu = QMenu(self.tipitems)
        colorAction = menu.addAction("Set Color")
        rootAction = menu.addAction("Root On")
        dropAction = menu.addAction("Drop Tips")
        action = menu.exec_(self.tipitems.mapToGlobal(pos))
        if action == rootAction:
            self.root_tree()
        elif action == colorAction:
            self.set_color()
        elif action == dropAction:
            self.drop_tips()

    def load_tree(self, filename):

        options = QFileDialog.Options()
        filter = "newick files (*.newick);;All files (*.*)"
        filename, _ = QFileDialog.getOpenFileName(self,"Open tree file",
                                    "",filter=filter,selectedFilter =filter, options=options)
        if not filename:
            return
        self.set_tree(toytree.tree(filename))
        return

    def set_tree(self, tree):
        """Set a new tree"""

        self.tree = tree
        self.colors = {}
        self.style['tip_labels_colors'] = 'black'
        self.tipitems.clear()
        for t in self.tree.get_tip_labels():
            item = QTreeWidgetItem(self.tipitems)
            item.setCheckState(1, QtCore.Qt.Checked)
            item.setText(0, t)

        return

    def update(self):
        """Update the plot"""

        if self.tree==None:
            return
        #set colors
        colorlist = [self.colors[tip] if tip in self.colors else "black" for tip in self.tree.get_tip_labels()]
        self.style['tip_labels_colors'] = colorlist
        canvas,axes,mark = self.tree.draw(
                        width=self.width,
                        height=self.height,
                        scalebar=True, **self.style)
        toyplot.html.render(canvas, "temp.html")
        with open('temp.html', 'r') as f:
            html = f.read()
            self.browser.setHtml(html)
        self.canvas = canvas
        return

    def root_tree(self):

        item = self.tipitems.selectedItems()[0]
        row = self.tipitems.selectedIndexes()[0].row()
        name = item.text(0)
        self.tree = self.tree.root(name).ladderize()
        self.update()
        return

    def unroot_tree(self):

        self.tree = self.tree.unroot().ladderize()
        self.update()
        return

    def export_image(self):
        """Save tree as image"""

        options = QFileDialog.Options()
        filter = "png files (*.png);;pdf files (*.pdf);;All files (*.*)"
        filename, _ = QFileDialog.getSaveFileName(self,"Save Project",
                                    "",filter=filter,selectedFilter =filter, options=options)
        if not filename:
            return

        ext = os.path.splitext(filename)
        print (ext)
        from toyplot import png
        png.render(self.canvas, filename, width=(4, "inches"))
        return

    def zoom(self):
        zoom = self.zoomslider.value()/10
        self.browser.setZoomFactor(zoom)

    def tree_style_options(self):

        fonts = ['%spx' %i for i in range (6,28)]
        markers = ['o','s','d','^','>']
        nlabels = ['','idx','support']
        tip_labels_style = self.style['tip_labels_style']

        opts = {
                'layout': {'type':'combobox','default':self.style['layout'],'items':['r','d','c']},
                'edge_type': {'type':'combobox','default':self.style['edge_type'],'items':['p','c']},
                'tip_labels':{'type':'checkbox','default':self.style['tip_labels'] },
                'tip_labels_align':{'type':'checkbox','default':self.style['tip_labels_align'] },
                'node_labels':{'type':'combobox','default':self.style['node_labels'],'items': nlabels},
                'node_sizes':{'type':'spinbox','default':self.style['node_sizes'],'range':(2,20),'interval':1},
                'node_markers': {'type':'combobox','default':self.style['node_markers'],'items':markers},
                'font_size':{'type':'combobox','default':tip_labels_style['font-size'],'items':fonts},
                'width':{'type':'entry','default':self.width},
                'height':{'type':'entry','default':self.height,},
                }

        dlg = MultipleInputDialog(self, opts, title='Tree Style', width=300)
        dlg.exec_()
        if not dlg.accepted:
            return False
        kwds = dlg.values
        self.set_style(kwds)
        self.update()
        return

    def set_style(self, kwds):

        omit=['width','height','font_size']
        for k in kwds:
            if k not in omit:
                self.style[k] = kwds[k]
        if kwds['node_labels'] == '':
            self.style['node_labels'] = False
        self.style['tip_labels_style']['font-size'] = kwds['font_size']
        self.width = kwds['width']
        self.height = kwds['height']
        self.tree = self.tree.ladderize()
        return

    def reset_style(self):

        self.style = self.default_style
        self.colors = {}
        print (self.style)
        self.update()

    def set_color(self, kind='text'):

        items = self.tipitems.selectedItems()
        names = [i.text(0) for i in items]
        qcolor = QColorDialog.getColor()
        for item in items:
            item.setBackground(0 , qcolor)
        for name in names:
            if kind == 'text':
                self.colors[name] = qcolor.name()
            elif kind == 'node':
                self.node_colors[name] = qcolor.name()
        self.update()
        return

    def drop_tips(self):

        items = self.tipitems.selectedItems()
        names = [i.text(0) for i in items]
        #for name in names:
        self.tree = self.tree.drop_tips(names=names).ladderize()
        self.update()
        return

class MultipleInputDialog(QDialog):
    """Qdialog with multiple inputs"""
    def __init__(self, parent, options=None, title='Input', width=400, height=200):
        super(MultipleInputDialog, self).__init__(parent)
        self.values = None
        self.accepted = False
        self.setMinimumSize(width, height)
        self.setWindowTitle(title)
        dialog, self.widgets = dialogFromOptions(self, options)
        vbox = QVBoxLayout(self)
        vbox.addWidget(dialog)
        buttonbox = QDialogButtonBox(self)
        buttonbox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        buttonbox.button(QDialogButtonBox.Ok).clicked.connect(self.accept)
        buttonbox.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        vbox.addWidget(buttonbox)
        self.show()
        return self.values

    def accept(self):
        self.values = getWidgetValues(self.widgets)
        self.accepted = True
        self.close()
        return

def dialogFromOptions(parent, opts, sections=None,
                      sticky='news', wrap=2, section_wrap=2):
    """Get Qt widgets dialog from a dictionary of options"""

    sizepolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    sizepolicy.setHorizontalStretch(1)
    sizepolicy.setVerticalStretch(0)

    style = '''
    QLabel {
        font-size: 12px;
    }
    QWidget {
        max-width: 130px;
        min-width: 30px;
        font-size: 14px;
    }
    QPlainTextEdit {
        max-height: 80px;
    }
    '''

    if sections == None:
        sections = {'options': opts.keys()}

    widgets = {}
    dialog = QWidget(parent)
    dialog.setSizePolicy(sizepolicy)

    l = QGridLayout(dialog)
    l.setSpacing(2)
    l.setAlignment(QtCore.Qt.AlignLeft)
    scol=1
    srow=1
    for s in sections:
        row=1
        col=1
        f = QGroupBox()
        f.setSizePolicy(sizepolicy)
        f.setTitle(s)
        #f.resize(50,100)
        #f.sizeHint()
        l.addWidget(f,srow,scol)
        gl = QGridLayout(f)
        gl.setAlignment(QtCore.Qt.AlignTop)
        srow+=1
        #gl.setSpacing(10)
        for o in sections[s]:
            label = o
            val = None
            opt = opts[o]
            if 'label' in opt:
                label = opt['label']
            val = opt['default']
            t = opt['type']
            lbl = QLabel(label)
            gl.addWidget(lbl,row,col)
            lbl.setStyleSheet(style)
            if t == 'combobox':
                w = QComboBox()
                w.addItems(opt['items'])
                #w.view().setMinListWidth(100)
                try:
                    w.setCurrentIndex(opt['items'].index(str(opt['default'])))
                except:
                    w.setCurrentIndex(0)
            elif t == 'entry':
                w = QLineEdit()
                w.setText(str(val))
            elif t == 'textarea':
                w = QPlainTextEdit()
                #w.setSizePolicy(sizepolicy)
                w.insertPlainText(str(val))
            elif t == 'slider':
                w = QSlider(QtCore.Qt.Horizontal)
                s,e = opt['range']
                w.setTickInterval(opt['interval'])
                w.setSingleStep(opt['interval'])
                w.setMinimum(s)
                w.setMaximum(e)
                w.setTickPosition(QSlider.TicksBelow)
                w.setValue(val)
            elif t == 'spinbox':
                if type(val) is float:
                    w = QDoubleSpinBox()
                else:
                    w = QSpinBox()
                w.setValue(val)
                if 'range' in opt:
                    min,max=opt['range']
                    w.setRange(min,max)
                    w.setMinimum(min)
                if 'interval' in opt:
                    w.setSingleStep(opt['interval'])
            elif t == 'checkbox':
                w = QCheckBox()
                w.setChecked(val)
            elif t == 'font':
                w = QFontComboBox()
                w.resize(w.sizeHint())
                w.setCurrentIndex(1)
            col+=1
            gl.addWidget(w,row,col)
            w.setStyleSheet(style)
            widgets[o] = w
            #print (o, row, col)
            if col>=wrap:
                col=1
                row+=1
            else:
                col+=2
        if scol >= section_wrap:
            scol=1
        else:
            scol+=1
    return dialog, widgets

def getWidgetValues(widgets):
    """Get values back from a set of widgets"""

    kwds = {}
    for i in widgets:
        val = None
        if i in widgets:
            w = widgets[i]
            if type(w) is QLineEdit:
                try:
                    val = float(w.text())
                except:
                    val = w.text()
            elif type(w) is QPlainTextEdit:
                val = w.toPlainText()
            elif type(w) is QComboBox or type(w) is QFontComboBox:
                val = w.currentText()
            elif type(w) is QCheckBox:
                val = w.isChecked()
            elif type(w) is QSlider:
                val = w.value()
            elif type(w) in [QSpinBox,QDoubleSpinBox]:
                val = w.value()
            if val != None:
                kwds[i] = val
    kwds = kwds
    return kwds

def setWidgetValues(widgets, values):
    """Set values for a set of widgets from a dict"""

    kwds = {}
    for i in values:
        val = values[i]
        if i in widgets:
            #print (i, val, type(val))
            w = widgets[i]
            if type(w) is QLineEdit:
                w.setText(str(val))
            elif type(w) is QPlainTextEdit:
                w.insertPlainText(str(val))
            elif type(w) is QComboBox or type(w) is QFontComboBox:
                w.setCurrentIndex(1)
            elif type(w) is QCheckBox:
                w.setChecked(val)
            elif type(w) is QSlider:
                w.setValue(val)
            elif type(w) is QSpinBox:
                w.setValue(val)
    return

def main():
    "Run the application"

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    aw = TreeViewer()
    aw.show()
    app.exec_()

if __name__ == '__main__':
    main()
