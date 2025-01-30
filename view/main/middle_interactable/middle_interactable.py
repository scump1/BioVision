from PySide6.QtWidgets import QVBoxLayout, QMdiArea


class MiddleInteractable(QVBoxLayout):

    def __init__(self):

        super().__init__()

    def interactable(self):

        self.mdi_area = QMdiArea()

        self.addWidget(self.mdi_area)

        return self