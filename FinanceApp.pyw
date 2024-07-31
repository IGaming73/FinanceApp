import PyQt5.QtWidgets as Qt  # interface
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal  # signals
import os  # os interaction
import sys  # system functions
import json  # handle json data
import darkdetect  # detect dark mode
import locale  # region settings
from tkinter import filedialog  # file choosing ui


class FinanceApp(Qt.QMainWindow):
    """App to track the piggy bank money ammount"""

    class AskSettings(Qt.QWidget):
        """Popup to ask the base settings"""
        done = pyqtSignal(dict)
        closed = pyqtSignal()

        def start(self):
            super().__init__()
            self.isClosed = False
            self.setWindowTitle("Settings")
            self.setWindowIcon(QtGui.QIcon("assets\\icon.png"))
            self.buildUi()
            self.show()
        
        def buildUi(self):
            """Build the popup UI"""
            self.mainLayout = Qt.QVBoxLayout()
            self.setLayout(self.mainLayout)

            with open("currencies.json", "r", encoding="utf-8") as currenciesFile:
                self.currencies = json.load(currenciesFile)
            
            self.currencyWidget = Qt.QWidget()
            self.currencyLayout = Qt.QHBoxLayout()
            self.currencyWidget.setLayout(self.currencyLayout)
            self.mainLayout.addWidget(self.currencyWidget)

            self.currencyLabel = Qt.QLabel(text="Select currency:")
            self.currencyLabel.setFont(QtGui.QFont("Arial", 16))
            self.currencyLabel.setWordWrap(True)
            self.currencyLayout.addWidget(self.currencyLabel)
            
            self.currencySelect = Qt.QComboBox()
            self.currencySelect.setFont(QtGui.QFont("Arial", 16))
            self.currencySelect.setFixedHeight(40)
            self.labeledCurrencies = [f"{currency} ({currencyData['symbol']})" for currency, currencyData in self.currencies.items()]
            self.currencySelect.addItems(self.labeledCurrencies)
            self.currencyLayout.addWidget(self.currencySelect)

            self.doneButton = Qt.QPushButton(text="Done")
            self.doneButton.setFixedHeight(50)
            self.doneButton.setFont(QtGui.QFont("Arial", 20))
            self.mainLayout.addWidget(self.doneButton)
            self.doneButton.clicked.connect(self.doneClicked)
        
        def doneClicked(self):
            """Executes when the done button is pressed"""
            self.done.emit({"currency": self.currencySelect.currentText().split("(")[0][:-1]})
            self.isClosed = True
            self.close()
        
        def closeEvent(self, event):
            """Executes when the window is closed"""
            if not self.isClosed:
                self.closed.emit()
    

    def start(self):
        """Starts the app"""
        super().__init__()
        self.getData()
        self.checkSettings()
    
    def checkSettings(self):
        """Asks for the settings on first session"""
        def done(settings:dict):
            with open("data.json", "w", encoding="utf-8") as dataFile:
                json.dump({"settings": {"name": "", "currency": settings["currency"]},
                           "transactions": [],
                           "loans": []}, dataFile, indent=4)
            with open("data.json", "r", encoding="utf-8") as dataFile:
                self.data = json.load(dataFile)
            self.loadApp()
        
        def closed():
            self.checkSettings()

        if not self.data:
            self.askSettingsPopup = self.AskSettings()
            self.askSettingsPopup.start()
            self.askSettingsPopup.done.connect(done)
            self.askSettingsPopup.closed.connect(closed)
        else:
            self.loadApp()
    
    def loadApp(self):
        """Loads the app"""
        self.setWindowTitle("FinanceApp")
        self.setWindowIcon(QtGui.QIcon("assets\\icon.png"))
        self.defineVariables()
        self.buildUi()
        self.configureUi()
        self.showMaximized()
        self.show()
    
    def getData(self):
        """Reads the data and create files if necessary"""
        if not os.path.exists("data.json"):
            with open("data.json", "w", encoding="utf-8") as dataFile:
                json.dump({}, dataFile, indent=4)
        with open("data.json", "r", encoding="utf-8") as dataFile:
            try:
                self.data = json.load(dataFile)
            except json.decoder.JSONDecodeError:
                self.data = {}
        with open("currencies.json", "r", encoding="utf-8") as currenciesFile:
            self.currencies = json.load(currenciesFile)
    
    def defineVariables(self):
        """Define some variables that will be useful"""
        self.currency = self.data["settings"]["currency"]
        self.currencyData = self.currencies[self.currency]
        locale.setlocale(locale.LC_ALL, "")
    
    def buildUi(self):
        """Builds the main app UI"""
        # base layout
        self.centralAppWidget = Qt.QWidget()
        self.setCentralWidget(self.centralAppWidget)
        self.mainLayout = Qt.QHBoxLayout(self.centralAppWidget)

        # secondary widgets and layouts
        self.interactWidget = Qt.QWidget()
        self.notesWidget = Qt.QWidget()
        self.historyWidget = Qt.QWidget()

        self.interactLayout = Qt.QVBoxLayout()
        self.interactLayout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
        self.notesLayout = Qt.QVBoxLayout()
        self.notesLayout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
        self.historyLayout = Qt.QVBoxLayout()
        self.historyLayout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        self.interactWidget.setLayout(self.interactLayout)
        self.notesWidget.setLayout(self.notesLayout)
        self.historyWidget.setLayout(self.historyLayout)

        # creating the splitter
        self.splitter = Qt.QSplitter(QtCore.Qt.Horizontal)
        self.mainLayout.addWidget(self.splitter)
        self.splitter.addWidget(self.interactWidget)
        self.splitter.addWidget(self.notesWidget)
        self.splitter.addWidget(self.historyWidget)
        self.splitter.setSizes([250, 350, 400])

        self.buildInteract()
    
    def buildInteract(self):
        """Builds the interactWidget zone"""
        # build the main zones
        self.statusWidget = Qt.QWidget()
        self.statusLayout = Qt.QVBoxLayout()
        self.statusLayout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
        self.statusWidget.setLayout(self.statusLayout)
        self.interactLayout.addWidget(self.statusWidget)

        self.interactLayout.addSpacing(50)

        self.optionsWidget = Qt.QWidget()
        self.optionsLayout = Qt.QVBoxLayout()
        self.optionsLayout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
        self.optionsWidget.setLayout(self.optionsLayout)
        self.interactLayout.addWidget(self.optionsWidget)

        # build the status widget
        self.usernameInput = Qt.QLineEdit(text=self.data["settings"]["name"])
        self.usernameInput.setPlaceholderText("Username")
        self.usernameInput.setFont(QtGui.QFont("Arial", 20))
        self.usernameInput.setFixedHeight(50)
        self.statusLayout.addWidget(self.usernameInput)
        self.statusLayout.addSpacing(20)

        self.balanceLabel = Qt.QLabel(text=f"{self.calculateAmmount()} {self.currencies[self.data['settings']['currency']]['symbol']}")
        self.balanceLabel.setFont(QtGui.QFont("Arial", 24))
        self.balanceLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.statusLayout.addWidget(self.balanceLabel)

        self.realBalanceLabel = Qt.QLabel(text=f"({self.calculateAmmount(realBalance=True)} {self.currencies[self.data['settings']['currency']]['symbol']} in bank)")
        self.realBalanceLabel.setFont(QtGui.QFont("Arial", 16))
        self.realBalanceLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.statusLayout.addWidget(self.realBalanceLabel)

        # build the options widget
        self.addMoneyButton = Qt.QPushButton(text="Transfer money")
        self.addMoneyButton.setFont(QtGui.QFont("Arial", 20))
        self.addMoneyButton.setFixedHeight(50)
        self.optionsLayout.addWidget(self.addMoneyButton)

        self.lendMoneyButton = Qt.QPushButton(text="Lend money")
        self.lendMoneyButton.setFont(QtGui.QFont("Arial", 20))
        self.lendMoneyButton.setFixedHeight(50)
        self.optionsLayout.addWidget(self.lendMoneyButton)

        self.trackLoansButton = Qt.QPushButton(text="Track loans")
        self.trackLoansButton.setFont(QtGui.QFont("Arial", 20))
        self.trackLoansButton.setFixedHeight(50)
        self.optionsLayout.addWidget(self.trackLoansButton)

        self.viewTransactionsButton = Qt.QPushButton(text="View transactions")
        self.viewTransactionsButton.setFont(QtGui.QFont("Arial", 20))
        self.viewTransactionsButton.setFixedHeight(50)
        self.optionsLayout.addWidget(self.viewTransactionsButton)

        # zone to change file
        self.filesWidget = Qt.QWidget()
        self.filesLayout = Qt.QHBoxLayout()
        self.filesWidget.setLayout(self.filesLayout)
        self.optionsLayout.addWidget(self.filesWidget)
        
        self.newFileButton = Qt.QPushButton(text="New")
        self.newFileButton.setFont(QtGui.QFont("Arial", 20))
        self.newFileButton.setFixedHeight(50)
        self.filesLayout.addWidget(self.newFileButton)

        self.exportFileButton = Qt.QPushButton(text="Export")
        self.exportFileButton.setFont(QtGui.QFont("Arial", 20))
        self.exportFileButton.setFixedHeight(50)
        self.filesLayout.addWidget(self.exportFileButton)

        self.importFileButton = Qt.QPushButton(text="Import")
        self.importFileButton.setFont(QtGui.QFont("Arial", 20))
        self.importFileButton.setFixedHeight(50)
        self.filesLayout.addWidget(self.importFileButton)

        self.buildNotes()
    
    def buildNotes(self):
        """Builds the UI on the notes widget"""
        self.notesValueWidgets = []

        self.noteScroll = Qt.QScrollArea()
        self.noteScroll.setWidgetResizable(True)
        self.noteScrollWidget = Qt.QWidget()
        self.noteScrollLayout = Qt.QVBoxLayout(self.noteScrollWidget)
        self.noteScroll.setWidget(self.noteScrollWidget)
        self.notesLayout.addWidget(self.noteScroll)
        self.noteScroll.setStyleSheet("QScrollArea {border: none;}")

        for note in self.currencyData["ammounts"]:
            noteWidget = Qt.QWidget()
            noteLayout = Qt.QHBoxLayout()
            noteLayout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter)
            noteWidget.setLayout(noteLayout)
            self.noteScrollLayout.addWidget(noteWidget)

            noteImage = Qt.QLabel()
            noteImage.setFixedWidth(125)
            pixmap = QtGui.QPixmap(f"assets\\money\\{self.data['settings']['currency']}\\{note}.png")
            resizedPixmap = pixmap.scaledToHeight(50, QtCore.Qt.SmoothTransformation)
            noteImage.setPixmap(resizedPixmap)
            noteLayout.addWidget(noteImage)

            valueLabel = Qt.QLabel(text=f"{note} {self.currencyData["symbol"]}")
            valueLabel.setFont(QtGui.QFont("Arial", 20))
            valueLabel.setFixedWidth(100)
            noteLayout.addWidget(valueLabel)

            colonLabel = Qt.QLabel(text=":")
            colonLabel.setFont(QtGui.QFont("Arial", 20))
            colonLabel.setFixedWidth(20)
            noteLayout.addWidget(colonLabel)

            self.notesValueWidgets.append(Qt.QLabel(text="0"))
            self.notesValueWidgets[-1].setFont(QtGui.QFont("Arial", 20))
            noteLayout.addWidget(self.notesValueWidgets[-1])

        self.buildHistory()
    
    def buildHistory(self):
        """Builds the UI on the history widget"""
        self.historyLabelWidget = Qt.QWidget()
        self.historyLabelLayout = Qt.QHBoxLayout()
        self.historyLabelLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.historyLabelWidget.setLayout(self.historyLabelLayout)
        self.historyLayout.addWidget(self.historyLabelWidget)

        self.historyLabelLayout.addStretch()
        self.historyLabel = Qt.QLabel(text="Quick transactions history")
        self.historyLabel.setFont(QtGui.QFont("Arial", 20))
        self.historyLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.historyLabelLayout.addWidget(self.historyLabel)
        self.historyLayout.addSpacing(50)
        self.historyLabelLayout.addStretch()

        self.historyListWidget = Qt.QWidget()
        self.historyListLayout = Qt.QVBoxLayout()
        self.historyListWidget.setLayout(self.historyListLayout)
        self.historyLayout.addWidget(self.historyListWidget)
    
    def calculateMoney(self) -> list:
        """returns a list with the total money, actual possessed money, and a dict of every notes"""
        totalMoney, possessedMoney = 0, 0
        notes = {note: 0 for note in self.currencyData["ammounts"]}
        transactions, loans = self.data["transactions"], self.data["loans"]
        for transaction in transactions:
            for note, change in transaction["notes"].items():
                notes[note] += change
                totalMoney += change*float(note)
        possessedMoney = totalMoney
        #TODO: loan calculations
        for loan in loans:
            for note, change in loan["notes"].items():
                notes[note] += change
                if loan["repaid"]:
                    notes[note] += loan["repaid"][note]

    
    def configureUi(self):
        """Connects and makes the widgets functional"""
        pass

    def calculateAmmount(self, realBalance:bool=False) -> float:
        """Calculates the total amount of money from the notes and coins, deducting any outstanding loans"""
        #TODO: placeholder value
        return 127.12



if __name__ == "__main__":
    App = Qt.QApplication(sys.argv)
    App.setStyle("fusion")
    if darkdetect.isDark():  # if using dark mode
        # dark mode style found online
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
        palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
        palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
        palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.black)
        palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
        palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
        palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
        App.setPalette(palette)
    Window = FinanceApp()
    Window.start()
    App.exec_()
