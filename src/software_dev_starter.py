import sys
import os
import subprocess
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QLabel, QLineEdit, QProgressBar, QCheckBox, 
                             QFileDialog, QTextEdit, QGroupBox, QHBoxLayout)
from PyQt5.QtCore import pyqtSignal, QThread, pyqtSlot

# Initialize logging
logging.basicConfig(level=logging.INFO, filename='setup.log', filemode='w', 
                    format='%(name)s - %(levelname)s - %(message)s')

class SetupThread(QThread):
    """
    This thread handles the setup process in the background.
    """
    update_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, folder, libs, additional_libs):
        QThread.__init__(self)
        self.folder = folder
        self.libs = libs
        self.additional_libs = additional_libs

    def run(self):
        try:
            if not os.path.isdir(self.folder):
                raise Exception("Invalid folder path")

            os.chdir(self.folder)

            # Create and activate virtual environment
            self.update_signal.emit("Creating virtual environment...")
            self.createAndActivateVenv()

            # Update pip
            self.update_signal.emit("Updating pip...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

            # Create src folder
            self.update_signal.emit("Creating src folder...")
            os.makedirs("src", exist_ok=True)

            # Install libraries
            for lib in self.libs + self.additional_libs:
                if lib.strip():
                    self.update_signal.emit(f"Installing {lib}...")
                    subprocess.run([sys.executable, "-m", "pip", "install", lib.strip()])

            self.update_signal.emit("Setup complete!")

        except Exception as e:
            self.error_signal.emit(str(e))
            logging.error("Error in setup process: " + str(e))

    def createAndActivateVenv(self):
        """
        Create and activate a virtual environment based on the operating system.
        """
        venv_path = os.path.join(self.folder, 'venv')
        
        if not os.path.exists(venv_path):
            self.update_signal.emit("Creating virtual environment...")
            if sys.platform == "win32":
                subprocess.run(["python", "-m", "venv", "venv"])
            else:
                subprocess.run(["python3", "-m", "venv", "venv"])
        else:
            self.update_signal.emit("Virtual environment already exists.")

        activate_command = ".\\venv\\Scripts\\activate" if sys.platform == "win32" else "source venv/bin/activate"
        subprocess.run(activate_command, shell=True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Create label for window
        #self.titleLabel = QLabel('Software Dev Setup Tool', self)

        # Define folderInput here before it's used anywhere else
        self.folderInput = QLineEdit(self)
        # Ensure browseButton is defined here
        self.browseButton = QPushButton('Browse', self)
        # Ensure startButton is defined here
        self.startButton = QPushButton('Start', self)
        # Define progressBar here
        self.progressBar = QProgressBar(self)
        # Define messageArea here
        self.messageArea = QTextEdit(self)
        self.messageArea.setReadOnly(True)
        # Main layout
        mainLayout = QVBoxLayout()

        # Horizontal layout for two columns of categories
        categoriesLayout = QHBoxLayout()

        # Left column for first half of the categories
        leftColumn = QVBoxLayout()
        leftColumn.addWidget(self.createCategoryGroup("Math/Data Science", ["numpy", "pandas", "scikit-learn"]))
        leftColumn.addWidget(self.createCategoryGroup("Web Development", ["flask", "beautifulsoup4", "requests"]))
        leftColumn.addWidget(self.createCategoryGroup("Visualization", ["matplotlib"]))

        # Right column for second half of the categories
        rightColumn = QVBoxLayout()
        rightColumn.addWidget(self.createCategoryGroup("GUI Development", ["PyQt5"]))
        rightColumn.addWidget(self.createCategoryGroup("Database", ["sqlalchemy"]))
        rightColumn.addWidget(self.createCategoryGroup("Software Development Tools", ["pyinstaller"]))

        # Add the two columns to the categories layout
        categoriesLayout.addLayout(leftColumn)
        categoriesLayout.addLayout(rightColumn)

        # Add categories layout to the main layout
        mainLayout.addLayout(categoriesLayout)

        # Other Libraries
        self.additionalLibsInput = QLineEdit(self)
        self.additionalLibsInput.setPlaceholderText("Enter additional libraries, separated by commas")
        otherGroup = QGroupBox("Other")
        otherLayout = QVBoxLayout()
        otherLayout.addWidget(self.additionalLibsInput)
        otherGroup.setLayout(otherLayout)
        mainLayout.addWidget(otherGroup)

        # Other GUI elements (folder selection, buttons, message area)
        mainLayout.addWidget(QLabel('Select Target Folder:'))
        mainLayout.addWidget(self.folderInput)
        mainLayout.addWidget(self.browseButton)
        mainLayout.addWidget(self.startButton)
        mainLayout.addWidget(self.progressBar)
        mainLayout.addWidget(self.messageArea)

        # Set main layout
        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

        # Signal Connections
        self.browseButton.clicked.connect(self.browseFolder)
        self.startButton.clicked.connect(self.startSetup)

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
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folderInput.setText(folder)

    def startSetup(self):
        target_folder = self.folderInput.text()
        additional_libs = self.additionalLibsInput.text().split(',')
        selected_libs = [cb.text() for cb in self.findChildren(QCheckBox) if cb.isChecked()]

        self.setupThread = SetupThread(target_folder, selected_libs, additional_libs)
        self.setupThread.update_signal.connect(self.updateProgress)
        self.setupThread.error_signal.connect(self.showError)
        self.setupThread.start()

    @pyqtSlot(str, result=str)
    def updateProgress(self, message):
        self.messageArea.append(message)  # Append message to the text area

    @pyqtSlot(str, result=str)
    def showError(self, error_message):
        self.messageArea.append("Error: " + error_message)  # Append error message to the text area

def main():
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
