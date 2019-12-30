#!/usr/bin/env python3

#Example for threaded processes in pyside2 app

import sys,os,subprocess,time,traceback
import random
from PySide2 import QtCore
from PySide2.QtWidgets import *
from PySide2.QtGui import *

class App(QDialog):
    """GUI Application using PySide2 widgets"""
    def __init__(self):
        QDialog.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setGeometry(QtCore.QRect(200, 200, 500, 500))
        self.threadpool = QtCore.QThreadPool()

        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.startbutton = QPushButton('START')
        self.startbutton.clicked.connect(self.run)
        layout.addWidget(self.startbutton)
        self.stopbutton = QPushButton('STOP')
        self.stopbutton.clicked.connect(self.stop)
        layout.addWidget(self.stopbutton)
        self.progressbar = QProgressBar(self)
        self.progressbar.setRange(0,1)
        layout.addWidget(self.progressbar)
        self.info = QTextEdit(self)
        self.info.append('Hello')
        layout.addWidget(self.info)
        return

    def progress_fn(self, msg):

        self.info.append(str(msg))        
        return

    def run_threaded_process(self, process, on_complete):
        """Execute a function in the background with a worker"""

        worker = Worker(fn=process)
        self.threadpool.start(worker)
        worker.signals.finished.connect(on_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.progressbar.setRange(0,0)
        return

    def test(self, progress_callback):
        total = 500
        for i in range(0,total):
            time.sleep(.2)
            x = random.randint(1,1e4)
            progress_callback.emit(x)
            if self.stopped == True:
                return

    def run(self):
        self.stopped = False
        self.run_threaded_process(self.test, self.completed)

    def stop(self):
        self.stopped=True
        return

    def completed(self):
        self.progressbar.setRange(0,1)
        return

#https://www.learnpyqt.com/courses/concurrent-execution/multithreading-pyqt-applications-qthreadpool/
class Worker(QtCore.QRunnable):
    """Worker thread for running background tasks."""

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs['progress_callback'] = self.signals.progress

    @QtCore.Slot()
    def run(self):
        try:
            result = self.fn(
                *self.args, **self.kwargs,
            )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class WorkerSignals(QtCore.QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        No data
    error
        `tuple` (exctype, value, traceback.format_exc() )
    result
        `object` data returned from processing, anything
    """
    finished = QtCore.Signal()
    error = QtCore.Signal(tuple)
    result = QtCore.Signal(object)
    progress = QtCore.Signal(int)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    aw = App()
    aw.show()
    app.exec_()
