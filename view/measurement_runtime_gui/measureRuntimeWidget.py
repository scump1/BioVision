
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QProgressBar, QLabel
from PySide6.QtCore import QTimer
from PySide6.QtGui import QCloseEvent

from operator_mod.eventbus.event_handler import EventManager
from operator_mod.logger.progress_logger import ProgressLogger

class MeasureRuntimeWidget(QWidget):

    def __init__(self) -> None:
        
        super().__init__()

        self.events = EventManager()

        self.progress_logger = ProgressLogger("Measurement")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updater)
        
    def setupWidget(self):

        self.mainlayout_wrapper = QVBoxLayout()

        self.mainlayout = QHBoxLayout()

        self.progressbar = QProgressBar()
        self.progressbar.setMaximum(100)
        self.progressbar.setMinimum(0)
        self.progressbar.setValue(0)

        self.timelabel = QLabel()
        self.timelabel.setText("Remaining estimated runtime: --:--:--")

        self.mainlayout.addWidget(self.timelabel)
        self.mainlayout.addWidget(self.progressbar)

        self.mainlayout_wrapper.addLayout(self.mainlayout)

        self.setLayout(self.mainlayout_wrapper)

        return self

    def start_progress(self):
        self.timer.start(1000)
        
    def stop_progress(self):
        self.timer.stop()
        
    def reset_progress(self):
        self.progressbar.setValue(0)

    def updater(self):

        progress = self.progress_logger.get_progress()

        self.progressbar.setValue(int(progress[0]))
        
        if int(progress[0]) >= 100:
            self.events.trigger_event("EndMeasurement")
            self.close()
        
    def closeEvent(self, event: QCloseEvent) -> None:

        try:
            if self.timer.isActive():
                self.timer.stop()

        finally:
            event.accept()