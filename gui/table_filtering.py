#!/usr/bin/env python3

"""
    Test table filtering with pyqt5 with dataframe model

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 3
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import sys,os
import numpy as np
import pandas as pd
import geopandas as gpd

from PySide2 import QtCore
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, QUrl, QObject, Signal, Slot
from PySide2.QtWebEngineWidgets import QWebEngineView
from pandas.api.types import is_datetime64_any_dtype as is_datetime

class DataFrameModel(QtCore.QAbstractTableModel):
    def __init__(self, dataframe=None, *args):
        super(DataFrameModel, self).__init__()
        if dataframe is None:
            self.df = pd.DataFrame()
        else:
            self.df = dataframe
        self.bg = '#F4F4F3'
        self.rowcolors = None
        return

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        #if parent.isValid():
        #    return 0
        return len(self.df.columns.values)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Edit or display roles. Handles what happens when the Cells
        are edited or what appears in each cell.
        """

        i = index.row()
        j = index.column()
        #print (self.df.dtypes)
        #coltype = self.df.dtypes[j]
        coltype = self.df[self.df.columns[j]].dtype
        isdate = is_datetime(coltype)
        if role == QtCore.Qt.DisplayRole:
            value = self.df.iloc[i, j]
            if isdate:
                return value.strftime(core.TIMEFORMAT)
            elif type(value) != str:
                if type(value) in [float,np.float64] and np.isnan(value):
                    return ''
                elif type(value) == float:
                    return value
                else:
                    return (str(value))
            else:
                return '{0}'.format(value)
        elif (role == QtCore.Qt.EditRole):
            value = self.df.iloc[i, j]
            if type(value) is str:
                try:
                    return float(value)
                except:
                    return str(value)
            if np.isnan(value):
                return ''

    def headerData(self, col, orientation, role=QtCore.Qt.DisplayRole):
        """What's displayed in the headers"""

        if len(self.df.columns) == 0:
            return
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return str(self.df.columns[col])
            if orientation == QtCore.Qt.Vertical:
                value = self.df.index[col]
                if type( self.df.index) == pd.DatetimeIndex:
                    if not value is pd.NaT:
                        try:
                            return value.strftime(TIMEFORMAT)
                        except:
                            return ''
                else:
                    return str(value)
        return None

class DataFrameTable(QTableView):
    """
    QTableView with pandas DataFrame as model.
    """
    def __init__(self, parent=None, dataframe=None):

        QTableView.__init__(self)
        self.parent = parent
        vh = self.verticalHeader()
        vh.setVisible(True)
        vh.setDefaultSectionSize(28)
        vh.setMinimumWidth(20)
        vh.setMaximumWidth(500)

        hh = self.horizontalHeader()
        hh.setVisible(True)
        hh.setSectionsMovable(True)
        hh.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        hh.setSelectionBehavior(QTableView.SelectColumns)
        hh.setSelectionMode(QAbstractItemView.ExtendedSelection)
        #hh.sectionClicked.connect(self.columnClicked)
        hh.setSectionsClickable(True)

        self.resizeColumnsToContents()
        self.setCornerButtonEnabled(True)

        tm = DataFrameModel(dataframe)
        self.model = tm

        self.proxy = QtCore.QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.setModel(self.proxy)
        self.proxy.sort(0, Qt.AscendingOrder)
        self.setWordWrap(False)
        self.setCornerButtonEnabled(True)
        return

    def applyFilters(self, query):
        """Apply filter to table"""

        self.proxy.setFilterFixedString(query)
        return

class FilterWidget(QWidget):
    """Simple filtering for tables"""

    def __init__(self, parent, table, title=None):
        super(FilterWidget, self).__init__(parent)
        self.parent = parent
        self.table = table
        self.createWidgets()
        self.setMaximumHeight(200)
        return

    def createWidgets(self):
        """Create widgets"""

        style = '''
            QWidget {
                font-size: 12px;
            }
            QScrollBar:vertical {
                width: 15px;
                margin: 1px 0 1px 0;
            }
            QScrollBar::handle:vertical {
                min-height: 20px;
            }
            QComboBox {
                combobox-popup: 0;
                max-height: 30px;
                max-width: 150px;
            }
            '''

        df = self.table.model.df
        cols = list(df.columns)
        cols.insert(0,'Any')

        self.setWindowTitle('Search')
        #self.main = QWidget()
        self.setStyleSheet(style)
        self.setMaximumHeight(200)

        l = self.layout = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)
        w = self.queryedit = QLineEdit(self)
        w.returnPressed.connect(self.apply)

        l.addWidget(QLabel("Query:"))
        l.addWidget(w)

        w = QWidget()
        l.addWidget(w)
        hb = QHBoxLayout(w)
        hb.addWidget(QLabel('Column:'))
        w = self.searchcolw = QComboBox()
        w.addItems(cols)
        hb.addWidget(w)

        btn = QPushButton('Search')
        btn.clicked.connect(self.apply)
        l.addWidget(btn)
        return

    def closeEvent(self, ce):
        self.clear()

    def apply(self):
        """Apply filters"""

        df = self.table.model.df
        proxy = self.table.proxy
        searchcol = self.searchcolw.currentText()
        text = self.queryedit.text()
        if searchcol == 'Any':
            proxy.setFilterKeyColumn(-1)
        else:
            c = df.columns.get_loc(searchcol)
            proxy.setFilterKeyColumn(c)
        proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.table.applyFilters(text)
        return

    def clear(self):
        self.table.proxy.setFilterFixedString("")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(QtCore.QRect(100, 100, 800, 500))

        df = pd.read_csv('sample.csv')
        self.main = QWidget()
        layout = QVBoxLayout()
        #add table
        self.table = DataFrameTable(dataframe=df)
        layout.addWidget(self.table)
        #add filter widget
        self.filterw = FilterWidget(self, self.table)
        layout.addWidget(self.filterw)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
