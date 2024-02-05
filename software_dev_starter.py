import sys
import os
import subprocess
import threading
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QLabel, QLineEdit, QProgressBar, QCheckBox, 
                             QFileDialog, QTextEdit, QGroupBox, QHBoxLayout)
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot

# Initialize logging for debugging and tracking
logging.basicConfig(level=logging.INFO, filename='setup.log', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')

class SetupThread(QThread):
    """
    This thread handles the setup process in the background.
    """
    update_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, folder, libs, additional_libs, progressBar, messageArea, cancelFlag):
        QThread.__init__(self)
        self.folder = folder
        self.libs = libs
        self.additional_libs = additional_libs
        self.progressBar = progressBar
        self.messageArea = messageArea
        self.cancelFlag = cancelFlag
        self.totalSteps = 2 + len(libs) + len(additional_libs)
        self.completedSteps = 0

    def run(self):
        try:
            if not os.path.isdir(self.folder):
                raise Exception("Invalid folder path")
            os.chdir(self.folder)
            self.increment_progress("Navigating to folder...")

            self.createVenv()
            self.increment_progress("Creating virtual environment...")

            self.updatePip()
            self.installLibs()

            self.update_signal.emit("Setup complete!")

        except Exception as e:
            self.error_signal.emit(str(e))
            logging.error("Error in setup process: " + str(e))
            self.update_signal.emit(f"Error occurred: {str(e)}")

    def createVenv(self):
        # Create venv
        venv_path = os.path.join(self.folder, 'venv')
        if not os.path.exists(venv_path):
            subprocess.run(["python", "-m", "venv", "venv"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.increment_progress("Creating venv...")

    def updatePip(self):
        # Update pip
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.increment_progress("Updating pip...")

    def installLibs(self):
        # Create src folder
        os.makedirs("src", exist_ok=True)
        self.increment_progress("Creating src folder...")
        # Install libraries
        for lib in self.libs + self.additional_libs:
            if lib.strip():
                subprocess.run([sys.executable, "-m", "pip", "install", lib.strip()],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.increment_progress(f"Installing {lib}...")
                if self.cancelFlag.is_set():
                    self.update_signal.emit("Setup canceled.")
                    return

    def increment_progress(self, message):
        if self.cancelFlag.is_set():
            return
        self.completedSteps += 1
        progress = int((self.completedSteps / self.totalSteps) * 100)
        self.progressBar.setValue(progress)
        self.update_signal.emit(message)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.cancelFlag = threading.Event()

    def initUI(self):
        mainLayout = QVBoxLayout()

        # Two-column layout for categories
        categoriesLayout = QHBoxLayout()
        leftColumn, rightColumn = QVBoxLayout(), QVBoxLayout()
        # Add categories to leftColumn and rightColumn
        # Left column for the first half of the categories:
        leftColumn.addWidget(self.createCategoryGroup("Math/Data Science", ["numpy", "pandas", "scikit-learn"]))
        leftColumn.addWidget(self.createCategoryGroup("Web Development", ["flask", "beautifulsoup4", "requests", "streamlit"]))
        leftColumn.addWidget(self.createCategoryGroup("Visualization", ["matplotlib"]))
        # Righ column for second half of the categories:
        rightColumn.addWidget(self.createCategoryGroup("GUI Development", ["PyQt5", "PyQt5Designer"]))
        rightColumn.addWidget(self.createCategoryGroup("Database", ["sqlalchemy", "psycopg2"]))
        #rightColumn.addWidget(self.createCategoryGroup("Software Development Tools", ["pyinstaller", "pipreqs"]))
        # --Start-- Find the pipreqs checkbox and set it checked by default (replaces above line) --Start--
        devToolsGroup = self.createCategoryGroup("Software Development Tools", ["pyinstaller", "pipreqs"])
        for widget in devToolsGroup.findChildren(QCheckBox):
            if widget.text() == "pipreqs":
                widget.setChecked(True)
        rightColumn.addWidget(devToolsGroup)
        # --End-- Modification to add 'pipreqs' and set it to be auto-checked --End--
        categoriesLayout.addLayout(leftColumn)
        categoriesLayout.addLayout(rightColumn)
        mainLayout.addLayout(categoriesLayout)

        # Other Libraries input
        self.additionalLibsInput = QLineEdit(self)
        self.additionalLibsInput.setPlaceholderText("Enter additional libraries, separated by commas")
        otherGroup = QGroupBox("Other")
        otherLayout = QVBoxLayout()
        otherLayout.addWidget(self.additionalLibsInput)
        otherGroup.setLayout(otherLayout)
        mainLayout.addWidget(otherGroup)

        # Folder selection, buttons, progress bar, and message area
        self.folderInput = QLineEdit(self)
        self.browseButton = QPushButton('Browse', self)
        self.startButton = QPushButton('Start', self)
        self.cancelButton = QPushButton('Cancel', self)
        self.progressBar = QProgressBar(self)
        self.messageArea = QTextEdit(self)
        self.messageArea.setReadOnly(True)

        mainLayout.addWidget(QLabel('Select Target Folder:'))
        mainLayout.addWidget(self.folderInput)
        mainLayout.addWidget(self.browseButton)
        mainLayout.addWidget(self.startButton)
        mainLayout.addWidget(self.cancelButton)
        mainLayout.addWidget(self.progressBar)
        mainLayout.addWidget(self.messageArea)

        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

        # Connect signals to slots
        self.browseButton.clicked.connect(self.browseFolder)
        self.startButton.clicked.connect(self.startSetup)
        self.cancelButton.clicked.connect(self.cancelSetup)

    def createCategoryGroup(self, title, libraries):
        """
        Create a group box for a category of libraries.
        """
        group = QGroupBox(title)
        groupLayout = QVBoxLayout()
        for lib in libraries:
            checkbox = QCheckBox(lib, self)
            groupLayout.addWidget(checkbox)
        group.setLayout(groupLayout)
        return group

    def browseFolder(self):
        """
        Open a dialog for folder selection and update the folder input field.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folderInput.setText(folder)

    def startSetup(self):
        """
        Initiate the setup process in a separate thread.
        """
        target_folder = self.folderInput.text()
        additional_libs = self.additionalLibsInput.text().split(',')
        selected_libs = [cb.text() for cb in self.findChildren(QCheckBox) if cb.isChecked()]

        self.setupThread = SetupThread(target_folder, selected_libs, additional_libs,
                                       self.progressBar, self.messageArea, self.cancelFlag)
        self.setupThread.update_signal.connect(self.updateMessage)
        self.setupThread.error_signal.connect(self.showErrorMessage)
        self.setupThread.start()

    @pyqtSlot(str)
    def updateMessage(self, message):
        """
        Update the message area with the given message.
        """
        self.messageArea.append(message)

    @pyqtSlot(str)
    def showErrorMessage(self, error_message):
        """
        Display an error message in the message area.
        """
        self.messageArea.append("Error: " + error_message)

    def cancelSetup(self):
        """
        Signal the setup thread to stop the setup process.
        """
        self.cancelFlag.set()

def main():
    """
    Main function to start the application.
    """
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()