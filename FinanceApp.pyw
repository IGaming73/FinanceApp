import PyQt5.QtWidgets as Qt  # interface
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal  # signals
import os  # os interaction
import sys  # system functions
import json  # handle json data
import shutil  # system utilities
import ctypes  # system data
import locale  # language data
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

        def start(self, translations:dict, language:str):
            super().__init__()
            self.translations = translations
            self.language = language
            self.isClosed = False
            self.setWindowTitle(FinanceApp.translate(self, "settings", self.translations, self.language))
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

            self.currencyLabel = Qt.QLabel(text=FinanceApp.translate(self, "selectCurrency:", self.translations, self.language))
            self.currencyLabel.setFont(QtGui.QFont("Arial", 16))
            self.currencyLabel.setWordWrap(True)
            self.currencyLayout.addWidget(self.currencyLabel)
            
            self.currencySelect = Qt.QComboBox()
            self.currencySelect.setFont(QtGui.QFont("Arial", 16))
            self.currencySelect.setFixedHeight(40)
            self.labeledCurrencies = [f"{currency} ({currencyData['symbol']})" for currency, currencyData in self.currencies.items()]
            self.currencySelect.addItems(self.labeledCurrencies)
            self.currencyLayout.addWidget(self.currencySelect)

            self.doneButton = Qt.QPushButton(text=FinanceApp.translate(self, "done", self.translations, self.language))
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
        repaid = pyqtSignal(dict)
        applied = pyqtSignal(dict)

        def __init__(self, data:dict, moneyData:dict, currencyData:dict, translations:dict, language:str, lend:bool=False, repay:float=None):
            """Start creating interface"""
            self.data = data
            self.moneyData = moneyData
            self.currencyData = currencyData
            self.translations = translations
            self.language = language
            self.lending = lend
            self.repay = repay
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

            self.modifLabel = Qt.QLabel()
            self.modifLabel.setFont(QtGui.QFont("Arial", 24))
            self.infosLayout.addWidget(self.modifLabel)
            self.infosLayout.addSpacing(100)

            if self.repay is None:
                self.commentLabel = Qt.QLabel(text=FinanceApp.translate(self, "comment:", self.translations, self.language))
                self.commentLabel.setFont(QtGui.QFont("Arial", 20))
                self.infosLayout.addWidget(self.commentLabel)

                self.commentInput = Qt.QLineEdit()
                self.commentInput.setFont(QtGui.QFont("Arial", 20))
                self.commentInput.setPlaceholderText(FinanceApp.translate(self, "commentTransaction", self.translations, self.language))
                self.commentInput.setFixedHeight(50)
                self.infosLayout.addWidget(self.commentInput)
                self.infosLayout.addSpacing(50)

            self.cancelButton = Qt.QPushButton(text=FinanceApp.translate(self, "cancel", self.translations, self.language))
            self.cancelButton.setFont(QtGui.QFont("Arial", 20))
            self.cancelButton.setFixedHeight(50)
            self.infosLayout.addWidget(self.cancelButton)
            self.cancelButton.clicked.connect(self.canceled.emit)

            self.applyButton = Qt.QPushButton(text=FinanceApp.translate(self, "apply", self.translations, self.language))
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

                availableLabel = Qt.QLabel(text=FinanceApp.translate(self, "available:", self.translations, self.language))
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

                changeLabel = Qt.QLabel(text=FinanceApp.translate(self, "addRemove:", self.translations, self.language))
                changeLabel.setFont(QtGui.QFont("Arial", 20))
                noteLayout.addWidget(changeLabel)

                valueLabel = Qt.QLabel(text="0")
                valueLabel.setFont(QtGui.QFont("Arial", 20))
                valueLabel.setMinimumWidth(50)
                noteLayout.addWidget(valueLabel)
                self.valueLabels[note] = valueLabel

                removeButton = Qt.QPushButton()
                iconPath = "assets\\dark\\remove.png" if darkdetect.isDark() else "assets\\light\\remove.png"
                removeButton.setIcon(QtGui.QIcon(iconPath))
                removeButton.setIconSize(QtCore.QSize(40, 40))
                removeButton.setFixedSize(50, 50)
                noteLayout.addWidget(removeButton)
                removeButton.clicked.connect(functools.partial(self.removeClicked, note))

                noteLayout.addSpacing(10)

                addButton = Qt.QPushButton()
                iconPath = "assets\\dark\\add.png" if darkdetect.isDark() else "assets\\light\\add.png"
                addButton.setIcon(QtGui.QIcon(iconPath))
                addButton.setIconSize(QtCore.QSize(40, 40))
                addButton.setFixedSize(50, 50)
                noteLayout.addWidget(addButton)
                addButton.clicked.connect(functools.partial(self.addClicked, note))
            self.updateModif()
        
        def addClicked(self, note):
            """Adds one to the note"""
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
            if self.repay is None:
                self.totalModif = 0
                for note in self.currencyData["notes"]:
                    self.totalModif += float(self.valueLabels[note].text())*float(note)
                if self.totalModif == 0:
                    self.modifLabel.setText(FinanceApp.translate(self, "noAmmountModif", self.translations, self.language))
                elif self.totalModif > 0:
                    addingText = FinanceApp.translate(self, "borrowing", self.translations, self.language) if self.lending else FinanceApp.translate(self, "adding", self.translations, self.language)
                    self.modifLabel.setText(f"{addingText} {float(self.totalModif):.2f} {self.currencyData['symbol']} {FinanceApp.translate(self, "total", self.translations, self.language)}")
                else:
                    removingText = FinanceApp.translate(self, "lending", self.translations, self.language) if self.lending else FinanceApp.translate(self, "removing", self.translations, self.language)
                    self.modifLabel.setText(f"{removingText} {float(-1*self.totalModif):.2f} {self.currencyData['symbol']} {FinanceApp.translate(self, "total", self.translations, self.language)}")
            else:
                self.remainingAmmount = self.repay
                for note in self.currencyData["notes"]:
                    self.remainingAmmount += float(self.valueLabels[note].text())*float(note)
                if self.remainingAmmount == 0:
                    self.modifLabel.setText(FinanceApp.translate(self, "properlyRepaid", self.translations, self.language))
                elif self.remainingAmmount > 0:
                    texts = FinanceApp.translate(self, "repaidWithExcess", self.translations, self.language) if self.repay<=0 else FinanceApp.translate(self, "missingToRepay", self.translations, self.language)
                    self.modifLabel.setText(f"{texts[0]} {abs(float(self.remainingAmmount)):.2f} {self.currencyData['symbol']} {texts[1]}")
                else:
                    texts = FinanceApp.translate(self, "missingToRepay", self.translations, self.language) if self.repay<=0 else FinanceApp.translate(self, "repaidWithExcess", self.translations, self.language)
                    self.modifLabel.setText(f"{texts[0]} {abs(float(self.remainingAmmount)):.2f} {self.currencyData['symbol']} {texts[1]}")
        
        def apply(self):
            """Applies the modifications"""
            if self.repay is None:
                self.transferData = {}
                self.transferData["date"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                self.transferData["notes"] = {note:int(label.text()) for note, label in self.valueLabels.items()}
                self.transferData["comment"] = self.commentInput.text()
                if self.lending:
                    self.transferData["repaid"] = False
                self.applied.emit(self.transferData)
            else:
                if self.remainingAmmount != 0:
                    confirmation = Qt.QMessageBox.question(self, FinanceApp.translate(self, "confirmation", self.translations, self.language), FinanceApp.translate(self, "loanIncorrectWarning", self.translations, self.language), Qt.QMessageBox.Yes | Qt.QMessageBox.Cancel)
                    if confirmation != Qt.QMessageBox.Yes:
                        return
                self.repaid.emit({note:int(self.valueLabels[note].text()) for note in self.currencyData["notes"]})
    

    class ShowHistory(Qt.QWidget):
        """Widget that displays the detailed transaction history and allows to mark loans as payed"""
        back = pyqtSignal()
        repaid = pyqtSignal(dict)  # sends the whole modified data dict

        def __init__(self, data:dict, moneyData:dict, currencyData:dict, translations:dict, language:str):
            """Start creating interface"""
            self.data = data
            self.transactions = sorted(self.data["transactions"]+self.data["loans"], key=lambda transaction: datetime.datetime.strptime(transaction["date"], "%d/%m/%Y %H:%M:%S"), reverse=True)
            self.moneyData = moneyData
            self.currencyData = currencyData
            self.translations = translations
            self.language = language
            super().__init__()
            self.buildUi()
        
        def buildUi(self):
            """Builds the widget UI"""
            self.mainLayout = Qt.QVBoxLayout()
            self.setLayout(self.mainLayout)

            self.transactionScroll = Qt.QScrollArea()
            self.transactionScroll.setWidgetResizable(True)
            self.transactionScroll.setStyleSheet("QScrollArea {border: none;}")
            self.transactionWidget = Qt.QWidget()
            self.transactionLayout = Qt.QGridLayout()
            self.transactionLayout.setAlignment(QtCore.Qt.AlignTop)
            self.transactionScroll.setWidget(self.transactionWidget)
            self.transactionWidget.setLayout(self.transactionLayout)
            self.mainLayout.addWidget(self.transactionScroll)

            self.buttonWidget = Qt.QWidget()
            self.buttonLayout = Qt.QHBoxLayout()
            self.buttonLayout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignRight)
            self.buttonWidget.setLayout(self.buttonLayout)
            self.mainLayout.addWidget(self.buttonWidget)

            self.backButton = Qt.QPushButton(text=FinanceApp.translate(self, "back", self.translations, self.language))
            self.backButton.setFont(QtGui.QFont("Arial", 20))
            self.backButton.setFixedHeight(50)
            self.buttonLayout.addWidget(self.backButton)
            self.backButton.clicked.connect(self.back.emit)

            self.gridTexts = FinanceApp.translate(self, "gridTexts", self.translations, self.language)
            for i in range(len(self.gridTexts)):
                label = Qt.QLabel(text=self.gridTexts[i])
                label.setFont(QtGui.QFont("Arial", 20))
                self.transactionLayout.addWidget(label, 0, i)
            
            for i in range(len(self.transactions)):
                transaction = self.transactions[i]

                dateLabel = Qt.QLabel(text=transaction["date"])
                dateLabel.setFont(QtGui.QFont("Arial", 16))
                self.transactionLayout.addWidget(dateLabel, i+1, 0)

                actionText = FinanceApp.translate(self, "loan", self.translations, self.language) if "repaid" in transaction else FinanceApp.translate(self, "transaction", self.translations, self.language)
                actionLabel = Qt.QLabel(text=actionText)
                actionLabel.setFont(QtGui.QFont("Arial", 16))
                self.transactionLayout.addWidget(actionLabel)

                valueText = f"{FinanceApp.calculateMoneyTransaction(self, transaction):.2f} {self.currencyData["symbol"]}"
                valueLabel = Qt.QLabel(text=valueText)
                valueLabel.setFont(QtGui.QFont("Arial", 16))
                self.transactionLayout.addWidget(valueLabel)

                commentLabel = Qt.QLabel(text=transaction["comment"])
                commentLabel.setWordWrap(True)
                commentLabel.setFont(QtGui.QFont("Arial", 16))
                self.transactionLayout.addWidget(commentLabel)

                if "repaid" in transaction:
                    if not transaction["repaid"]:
                        repayButton = Qt.QPushButton(text=FinanceApp.translate(self, "repay", self.translations, self.language))
                        repayButton.setFont(QtGui.QFont("Arial", 16))
                        repayButton.setFixedHeight(40)
                        self.transactionLayout.addWidget(repayButton)
                        repayButton.clicked.connect(functools.partial(self.repay, transaction))
                
        def repay(self, transaction):
            """Repay a loan with given notes"""
            self.repayWidget = FinanceApp.TransferMoney(self.data, self.moneyData, self.currencyData, self.translations, self.language, repay=FinanceApp.calculateMoneyTransaction(self, transaction))
            FinanceApp.clear(self, self.mainLayout)
            self.mainLayout.addWidget(self.repayWidget)
            self.repayWidget.canceled.connect(self.back.emit)
            self.repayWidget.repaid.connect(lambda notes: self.applyRepay(transaction, notes))
        
        def applyRepay(self, transaction:dict, notes:dict):
            """Applies the repay"""
            for i in range(len(self.data["loans"])):
                if self.data["loans"][i] == transaction:
                    self.data["loans"][i]["repaid"] = notes
            self.repaid.emit(self.data)
            Qt.QMessageBox.information(self, FinanceApp.translate(self, "success", self.translations, self.language), FinanceApp.translate(self, "successRepaidText", self.translations, self.language), Qt.QMessageBox.Ok)
    


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

        if not self.data:
            self.askSettingsPopup = self.AskSettings()
            self.askSettingsPopup.start(self.translations, self.language)
            self.askSettingsPopup.done.connect(done)
            self.askSettingsPopup.closed.connect(self.checkSettings)
        else:
            self.loadApp()
    
    def translate(self, textId:str, translations:dict, language:str) -> str:
        """Gives the translation of the given word id"""
        if textId in translations:
            if language in translations[textId]:
                return translations[textId][language]
            else:
                return translations[textId]["en"]
        else:
            return textId
    
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
        with open("languages.json", "r", encoding="utf-8") as languagesFile:
            self.translations = json.load(languagesFile)
        windll = ctypes.windll.kernel32
        self.language = locale.windows_locale[windll.GetUserDefaultUILanguage()].split("_")[0]
    
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
        self.splitter.setSizes([200, 300, 500])

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
        self.usernameInput.setPlaceholderText(self.translate("username", self.translations, self.language))
        self.usernameInput.setFont(QtGui.QFont("Arial", 20))
        self.usernameInput.setFixedHeight(50)
        self.statusLayout.addWidget(self.usernameInput)
        self.statusLayout.addSpacing(20)

        self.balanceLabel = Qt.QLabel(text=f"{float(self.moneyData['total']):.2f} {self.currencyData['symbol']}")
        self.balanceLabel.setFont(QtGui.QFont("Arial", 24))
        self.balanceLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.statusLayout.addWidget(self.balanceLabel)

        self.realBalanceLabel = Qt.QLabel(text=f"({float(self.moneyData["possessed"]):.2f} {self.currencyData['symbol']} {self.translate("inBank", self.translations, self.language)})")
        self.realBalanceLabel.setFont(QtGui.QFont("Arial", 16))
        self.realBalanceLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.statusLayout.addWidget(self.realBalanceLabel)

        # build the options widget
        self.transferMoneyButton = Qt.QPushButton(text=self.translate("transferMoney", self.translations, self.language))
        self.transferMoneyButton.setFont(QtGui.QFont("Arial", 20))
        self.transferMoneyButton.setFixedHeight(50)
        self.optionsLayout.addWidget(self.transferMoneyButton)

        self.lendMoneyButton = Qt.QPushButton(text=self.translate("lendMoney", self.translations, self.language))
        self.lendMoneyButton.setFont(QtGui.QFont("Arial", 20))
        self.lendMoneyButton.setFixedHeight(50)
        self.optionsLayout.addWidget(self.lendMoneyButton)

        self.viewTransactionsButton = Qt.QPushButton(text=self.translate("viewTransactions", self.translations, self.language))
        self.viewTransactionsButton.setFont(QtGui.QFont("Arial", 20))
        self.viewTransactionsButton.setFixedHeight(50)
        self.optionsLayout.addWidget(self.viewTransactionsButton)

        # zone to change file
        self.filesWidget = Qt.QWidget()
        self.filesLayout = Qt.QHBoxLayout()
        self.filesWidget.setLayout(self.filesLayout)
        self.optionsLayout.addWidget(self.filesWidget)
        
        self.newFileButton = Qt.QPushButton(text=self.translate("new", self.translations, self.language))
        self.newFileButton.setFont(QtGui.QFont("Arial", 20))
        self.newFileButton.setFixedHeight(50)
        self.filesLayout.addWidget(self.newFileButton)

        self.exportFileButton = Qt.QPushButton(text=self.translate("export", self.translations, self.language))
        self.exportFileButton.setFont(QtGui.QFont("Arial", 20))
        self.exportFileButton.setFixedHeight(50)
        self.filesLayout.addWidget(self.exportFileButton)

        self.importFileButton = Qt.QPushButton(text=self.translate("import", self.translations, self.language))
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

        self.historyLabel = Qt.QLabel(text=self.translate("quickHistory", self.translations, self.language))
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
                if self.calculateMoneyTransaction(transaction) < 0:
                    loanText = self.translate("lent", self.translations, self.language)
                else:
                    loanText = self.translate("borrowed", self.translations, self.language)
                if transaction["repaid"]:
                    transactionText = f"{self.translate("loanRepaid", self.translations, self.language)} {loanText}"
                else:
                    transactionText = f"{self.translate("loanUnpaid", self.translations, self.language)} {loanText}"
            else:
                transactionText = self.translate("added", self.translations, self.language) if totalTransfer >= 0 else self.translate("removed", self.translations, self.language)
            transactionLabel = Qt.QLabel(text=f"{transaction["date"].split(" ")[0]}: {transactionText} {abs(totalTransfer):.2f} {self.currencyData["symbol"]}")
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
            baseLoan = 0
            for note, change in loan["notes"].items():
                notes[note] += change
                baseLoan += change*float(note)
            possessedMoney += baseLoan
            if loan["repaid"]:
                totalMoney += baseLoan
                for note, change in loan["repaid"].items():
                    notes[note] += change
                    changeValue = change*float(note)
                    totalMoney += changeValue
                    possessedMoney += changeValue

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
            self.transferMoneyWidget = self.TransferMoney(self.data, self.moneyData, self.currencyData, self.translations, self.language, lend=lend)
            self.transferMoneyWidget.canceled.connect(lambda: self.start(reloaded=True))
            self.transferMoneyWidget.applied.connect(self.applyTransfer)
            self.mainLayout.addWidget(self.transferMoneyWidget)
        
        def viewTransactions():
            self.clear(self.mainLayout)
            self.historyWidget = self.ShowHistory(self.data, self.moneyData, self.currencyData, self.translations, self.language)
            self.historyWidget.back.connect(lambda: self.start(reloaded=True))
            self.historyWidget.repaid.connect(repaid)
            self.mainLayout.addWidget(self.historyWidget)
        
        def repaid(newData):
            self.data = newData
            self.saveData()
            self.clear(self.mainLayout)
            self.start(reloaded=True)
        
        def newFile():
            confirmation = Qt.QMessageBox.question(self, self.translate("confirmation", self.translations, self.language), self.translate("newFileWarning", self.translations, self.language), Qt.QMessageBox.Yes | Qt.QMessageBox.Cancel)
            if confirmation == Qt.QMessageBox.Yes:
                os.remove("data.json")
                self.start(reloaded=True)
        
        def exportFile():
            exportPath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON file", "*.json")])
            if exportPath:
                shutil.copy("data.json", exportPath)
                Qt.QMessageBox.information(self, self.translate("success", self.translations, self.language), self.translate("exportedSuccessfully", self.translations, self.language))
        
        def importFile():
            importedFile = filedialog.askopenfilename(filetypes=[("JSON file", "*.json")])
            if importedFile:
                confirmation = Qt.QMessageBox.question(self, self.translate("confirmation", self.translations, self.language), self.translate("importWarning", self.translations, self.language), Qt.QMessageBox.Yes | Qt.QMessageBox.Cancel)
                if confirmation == Qt.QMessageBox.Yes:
                    os.remove("data.json")
                    shutil.copy(importedFile, "data.json")
                    self.start(reloaded=True)
                    Qt.QMessageBox.information(self, self.translate("success", self.translations, self.language), self.translate("importedSuccessfully", self.translations, self.language))

        self.usernameInput.editingFinished.connect(updateUsername)
        self.transferMoneyButton.clicked.connect(transferMoney)
        self.lendMoneyButton.clicked.connect(lambda: transferMoney(lend=True))
        self.viewTransactionsButton.clicked.connect(viewTransactions)
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
