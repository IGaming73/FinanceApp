import PyQt5.QtWidgets as Qt  # interface
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal  # signals
import os  # os interaction
import sys  # system functions
import json  # handle json data
import shutil  # system utilities
import darkdetect  # detect dark mode
import functools  # tools for functions
import datetime  # handle time
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
    

    class TransferMoney(Qt.QWidget):
        """Class for the interface to transfer money"""
        canceled = pyqtSignal()
        applied = pyqtSignal(dict)

        def __init__(self, data:dict, moneyData:dict, currencyData:dict, lend:bool=False):
            """Start creating interface"""
            self.data = data
            self.moneyData = moneyData
            self.currencyData = currencyData
            self.lending = lend
            super().__init__()
            self.buildUi()
        
        def buildUi(self):
            """Build the UI"""
            self.mainLayout = Qt.QVBoxLayout()
            self.setLayout(self.mainLayout)

            self.noteScroll = Qt.QScrollArea()
            self.noteScroll.setWidgetResizable(True)
            self.noteScrollWidget = Qt.QWidget()
            self.noteScrollLayout = Qt.QVBoxLayout(self.noteScrollWidget)
            self.noteScrollLayout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
            self.noteScroll.setWidget(self.noteScrollWidget)
            self.mainLayout.addWidget(self.noteScroll)
            self.noteScroll.setStyleSheet("QScrollArea {border: none;}")

            self.infosWidget = Qt.QWidget()
            self.infosLayout = Qt.QHBoxLayout()
            self.infosLayout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignRight)
            self.infosWidget.setLayout(self.infosLayout)
            self.mainLayout.addWidget(self.infosWidget)

            self.modifLabel = Qt.QLabel(text="No ammount modification")
            self.modifLabel.setFont(QtGui.QFont("Arial", 24))
            self.infosLayout.addWidget(self.modifLabel)
            self.infosLayout.addSpacing(100)

            self.commentLabel = Qt.QLabel(text="Comment: ")
            self.commentLabel.setFont(QtGui.QFont("Arial", 20))
            self.infosLayout.addWidget(self.commentLabel)

            self.commentInput = Qt.QLineEdit()
            self.commentInput.setFont(QtGui.QFont("Arial", 20))
            self.commentInput.setPlaceholderText("Comment on the transaction")
            self.commentInput.setFixedHeight(50)
            self.infosLayout.addWidget(self.commentInput)
            self.infosLayout.addSpacing(50)

            self.cancelButton = Qt.QPushButton(text="Cancel")
            self.cancelButton.setFont(QtGui.QFont("Arial", 20))
            self.cancelButton.setFixedHeight(50)
            self.infosLayout.addWidget(self.cancelButton)
            self.cancelButton.clicked.connect(self.canceled.emit)

            self.applyButton = Qt.QPushButton(text="Apply")
            self.applyButton.setFont(QtGui.QFont("Arial", 20))
            self.applyButton.setFixedHeight(50)
            self.infosLayout.addWidget(self.applyButton)
            self.applyButton.clicked.connect(self.apply)

            self.valueLabels = {}

            for note in self.currencyData["notes"]:
                noteWidget = Qt.QWidget()
                noteLayout = Qt.QHBoxLayout()
                noteLayout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter)
                noteWidget.setLayout(noteLayout)
                self.noteScrollLayout.addWidget(noteWidget)

                noteImage = Qt.QLabel()
                noteImage.setFixedWidth(120)
                pixmap = QtGui.QPixmap(f"assets\\money\\{self.data['settings']['currency']}\\{note}.png")
                resizedPixmap = pixmap.scaledToHeight(50, QtCore.Qt.SmoothTransformation)
                noteImage.setPixmap(resizedPixmap)
                noteLayout.addWidget(noteImage)

                valueLabel = Qt.QLabel(text=f"{note} {self.currencyData["symbol"]}")
                valueLabel.setFont(QtGui.QFont("Arial", 20))
                valueLabel.setMinimumWidth(90)
                noteLayout.addWidget(valueLabel)

                colonLabel = Qt.QLabel(text=":")
                colonLabel.setFont(QtGui.QFont("Arial", 20))
                colonLabel.setMinimumWidth(20)
                noteLayout.addWidget(colonLabel)

                availableLabel = Qt.QLabel(text="available:")
                availableLabel.setFont(QtGui.QFont("Arial", 20))
                noteLayout.addWidget(availableLabel)

                availableValueLabel = Qt.QLabel(text=str(self.moneyData["notes"][note]))
                availableValueLabel.setMinimumWidth(50)
                availableValueLabel.setFont(QtGui.QFont("Arial", 20))
                noteLayout.addWidget(availableValueLabel)

                semicolonLabel = Qt.QLabel(text=";")
                semicolonLabel.setFont(QtGui.QFont("Arial", 20))
                semicolonLabel.setMinimumWidth(20)
                noteLayout.addWidget(semicolonLabel)

                changeLabel = Qt.QLabel(text="add/remove:")
                changeLabel.setFont(QtGui.QFont("Arial", 20))
                noteLayout.addWidget(changeLabel)

                valueLabel = Qt.QLabel(text="0")
                valueLabel.setFont(QtGui.QFont("Arial", 20))
                valueLabel.setMinimumWidth(50)
                noteLayout.addWidget(valueLabel)
                self.valueLabels[note] = valueLabel

                removeButton = Qt.QPushButton()
                removeButton.setIcon(QtGui.QIcon("assets\\remove.png"))
                removeButton.setIconSize(QtCore.QSize(40, 40))
                removeButton.setFixedSize(50, 50)
                noteLayout.addWidget(removeButton)
                removeButton.clicked.connect(functools.partial(self.removeClicked, note))

                noteLayout.addSpacing(10)

                addButton = Qt.QPushButton()
                addButton.setIcon(QtGui.QIcon("assets\\add.png"))
                addButton.setIconSize(QtCore.QSize(40, 40))
                addButton.setFixedSize(50, 50)
                noteLayout.addWidget(addButton)
                addButton.clicked.connect(functools.partial(self.addClicked, note))
        
        def addClicked(self, note):
            """Adds one to the note"""
            #TODO: prevent borrowing money
            val = int(self.valueLabels[note].text())
            val += 1
            self.valueLabels[note].setText(str(val))
            self.updateModif()

        def removeClicked(self, note):
            """Removes one to the note"""
            val = int(self.valueLabels[note].text())
            if val > -1*self.moneyData["notes"][note]:
                val -= 1
                self.valueLabels[note].setText(str(val))
                self.updateModif()
        
        def updateModif(self):
            """Updates the modifLabel text"""
            self.totalModif = 0
            for note in self.currencyData["notes"]:
                self.totalModif += float(self.valueLabels[note].text())*float(note)
            if self.totalModif == 0:
                self.modifLabel.setText("No ammount modification")
            elif self.totalModif > 0:
                addingText = "Loaning" if self.lending else "Adding"
                self.modifLabel.setText(f"{addingText} {float(self.totalModif):.2f} {self.currencyData['symbol']} total")
            else:
                removingText = "Lending" if self.lending else "Removing"
                self.modifLabel.setText(f"{removingText} {float(-1*self.totalModif):.2f} {self.currencyData['symbol']} total")
        
        def apply(self):
            """Applies the modifications"""
            self.transferData = {}
            self.transferData["date"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            self.transferData["notes"] = {note:int(label.text()) for note, label in self.valueLabels.items()}
            self.transferData["comment"] = self.commentInput.text()
            if self.lending:
                self.transferData["repaid"] = False
            self.applied.emit(self.transferData)
    


    def start(self, reloaded=False):
        """Starts the app"""
        self.reloaded = reloaded
        if not self.reloaded:
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
        self.defineVariables()
        self.buildUi()
        self.configureUi()
        if not self.reloaded:
            self.setWindowTitle("FinanceApp")
            self.setWindowIcon(QtGui.QIcon("assets\\icon.png"))
            self.setFocus()
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
        self.currencyData = {**{"name": self.data["settings"]["currency"]}, **self.currencies[self.data["settings"]["currency"]]}
        self.moneyData = self.calculateMoney()
    
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

        self.balanceLabel = Qt.QLabel(text=f"{float(self.moneyData['total']):.2f} {self.currencyData['symbol']}")
        self.balanceLabel.setFont(QtGui.QFont("Arial", 24))
        self.balanceLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.statusLayout.addWidget(self.balanceLabel)

        self.realBalanceLabel = Qt.QLabel(text=f"({float(self.moneyData["possessed"]):.2f} {self.currencyData['symbol']} in bank)")
        self.realBalanceLabel.setFont(QtGui.QFont("Arial", 16))
        self.realBalanceLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.statusLayout.addWidget(self.realBalanceLabel)

        # build the options widget
        self.transferMoneyButton = Qt.QPushButton(text="Transfer money")
        self.transferMoneyButton.setFont(QtGui.QFont("Arial", 20))
        self.transferMoneyButton.setFixedHeight(50)
        self.optionsLayout.addWidget(self.transferMoneyButton)

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
        self.noteScroll = Qt.QScrollArea()
        self.noteScroll.setWidgetResizable(True)
        self.noteScrollWidget = Qt.QWidget()
        self.noteScrollLayout = Qt.QVBoxLayout(self.noteScrollWidget)
        self.noteScrollLayout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
        self.noteScroll.setWidget(self.noteScrollWidget)
        self.notesLayout.addWidget(self.noteScroll)
        self.noteScroll.setStyleSheet("QScrollArea {border: none;}")

        for note in self.currencyData["notes"]:
            noteWidget = Qt.QWidget()
            noteLayout = Qt.QHBoxLayout()
            noteLayout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter)
            noteWidget.setLayout(noteLayout)
            self.noteScrollLayout.addWidget(noteWidget)

            noteImage = Qt.QLabel()
            noteImage.setFixedWidth(120)
            pixmap = QtGui.QPixmap(f"assets\\money\\{self.data['settings']['currency']}\\{note}.png")
            resizedPixmap = pixmap.scaledToHeight(50, QtCore.Qt.SmoothTransformation)
            noteImage.setPixmap(resizedPixmap)
            noteLayout.addWidget(noteImage)

            valueLabel = Qt.QLabel(text=f"{note} {self.currencyData["symbol"]}")
            valueLabel.setFont(QtGui.QFont("Arial", 20))
            valueLabel.setMinimumWidth(90)
            noteLayout.addWidget(valueLabel)

            colonLabel = Qt.QLabel(text=":")
            colonLabel.setFont(QtGui.QFont("Arial", 20))
            colonLabel.setMinimumWidth(20)
            noteLayout.addWidget(colonLabel)

            valueLabel = Qt.QLabel(text=str(self.moneyData["notes"][note]))
            valueLabel.setFont(QtGui.QFont("Arial", 20))
            noteLayout.addWidget(valueLabel)

        self.buildHistory()
    
    def buildHistory(self):
        """Builds the UI on the history widget"""
        self.historyScroll = Qt.QScrollArea()
        self.historyScroll.setWidgetResizable(True)
        self.historyScrollWidget = Qt.QWidget()
        self.historyScrollLayout = Qt.QVBoxLayout(self.historyScrollWidget)
        self.historyScrollLayout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
        self.historyScroll.setWidget(self.historyScrollWidget)
        self.historyLayout.addWidget(self.historyScroll)
        self.historyScroll.setStyleSheet("QScrollArea {border: none;}")

        self.historyLabelWidget = Qt.QWidget()
        self.historyLabelLayout = Qt.QHBoxLayout()
        self.historyLabelWidget.setLayout(self.historyLabelLayout)
        self.historyScrollLayout.addWidget(self.historyLabelWidget)

        self.historyLabel = Qt.QLabel(text="Quick transactions history")
        self.historyLabel.setFont(QtGui.QFont("Arial", 24))
        self.historyLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.historyLabelLayout.addWidget(self.historyLabel)
        self.historyScrollLayout.addSpacing(50)

        self.historyListWidget = Qt.QWidget()
        self.historyListLayout = Qt.QVBoxLayout()
        self.historyListWidget.setLayout(self.historyListLayout)
        self.historyScrollLayout.addWidget(self.historyListWidget)

        for transaction in sorted(self.data["transactions"]+self.data["loans"], key=lambda transaction: datetime.datetime.strptime(transaction.get("date", "01/01/1970 00:00:00"), "%d/%m/%Y %H:%M:%S"), reverse=True):
            totalTransfer = self.calculateMoneyTransaction(transaction)
            if "repaid" in transaction:
                if transaction["repaid"]:
                    transactionText = "loan: lent"
                else:
                    transactionText = "loan (unpaid): lent"
            else:
                transactionText = "added" if totalTransfer >= 0 else "removed"
            transactionLabel = Qt.QLabel(text=f"{transaction["date"].split(" ")[0]}: {transactionText} {abs(totalTransfer)} {self.currencyData["symbol"]}")
            transactionLabel.setFont(QtGui.QFont("Arial", 20))
            self.historyListLayout.addWidget(transactionLabel)
            self.historyListLayout.addSpacing(10)
    
    def calculateMoney(self) -> list:
        """returns a list with the total money, actual possessed money, and a dict of every notes"""
        totalMoney = 0
        notes = {note: 0 for note in self.currencyData["notes"]}
        transactions, loans = self.data["transactions"], self.data["loans"]
        for transaction in transactions:
            for note, change in transaction["notes"].items():
                notes[note] += change
                totalMoney += change*float(note)
        possessedMoney = totalMoney
        
        for loan in loans:
            for note, change in loan["notes"].items():
                notes[note] += change
                possessedMoney += change*float(note)
            if loan["repaid"]:
                for note, change in loan["repaid"].items():
                    notes[note] += change
                    possessedMoney += change*float(note)

        return {"total": totalMoney, "possessed": possessedMoney, "notes": notes}
    
    def calculateMoneyTransaction(self, transaction:dict) -> float:
        """Calculates the change in money from a single transaction"""
        totalMoney = 0
        for note, change in transaction["notes"].items():
            totalMoney += change*float(note)
        return totalMoney

    
    def configureUi(self):
        """Connects and makes the widgets functional"""
        def updateUsername():
            self.data["settings"]["name"] = self.usernameInput.text()
            self.saveData()
        
        def transferMoney(lend=False):
            self.clear(self.mainLayout)
            self.transferMoneyWidget = self.TransferMoney(self.data, self.moneyData, self.currencyData, lend=lend)
            self.transferMoneyWidget.canceled.connect(lambda: self.start(reloaded=True))
            self.transferMoneyWidget.applied.connect(self.applyTransfer)
            self.mainLayout.addWidget(self.transferMoneyWidget)
        
        def newFile():
            confirmation = Qt.QMessageBox.question(self, "Confirmation", "Are you sure you want to create a new file?\nEvery unexported data will be lost!", Qt.QMessageBox.Yes | Qt.QMessageBox.Cancel)
            if confirmation == Qt.QMessageBox.Yes:
                os.remove("data.json")
                self.start(reloaded=True)
        
        def exportFile():
            exportPath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON file", "*.json")])
            if exportPath:
                shutil.copy("data.json", exportPath)
                Qt.QMessageBox.information(self, "Success", "Data exported successfully!")
        
        def importFile():
            importedFile = filedialog.askopenfilename(filetypes=[("JSON file", "*.json")])
            if importedFile:
                confirmation = Qt.QMessageBox.question(self, "Confirmation", "Are you sure you want to import this file?\nEvery unexported data will be lost!", Qt.QMessageBox.Yes | Qt.QMessageBox.Cancel)
                if confirmation == Qt.QMessageBox.Yes:
                    os.remove("data.json")
                    shutil.copy(importedFile, "data.json")
                    self.start(reloaded=True)
                    Qt.QMessageBox.information(self, "Success", "Data imported successfully!")

        self.usernameInput.editingFinished.connect(updateUsername)
        self.transferMoneyButton.clicked.connect(transferMoney)
        self.lendMoneyButton.clicked.connect(lambda: transferMoney(lend=True))
        self.newFileButton.clicked.connect(newFile)
        self.exportFileButton.clicked.connect(exportFile)
        self.importFileButton.clicked.connect(importFile)
    
    def applyTransfer(self, transferData:dict):
        """Applies the money transfer"""
        if "repaid" in transferData:
            self.data["loans"].append(transferData)
        else:
            self.data["transactions"].append(transferData)
        self.saveData()
        self.start(reloaded=True)
    
    def saveData(self):
        """Saves the data to the json file"""
        with open("data.json", "w", encoding="utf-8") as dataFile:
            json.dump(self.data, dataFile, indent=4)
    
    def clear(self, layout:Qt.QLayout):
        """clear the whole layout"""
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)  # delete widget



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
