# Add error handling to main.py
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from gui.app import App

def main():
    try:
        app = QApplication(sys.argv)
        ex = App()
        sys.exit(app.exec_())
    except ImportError as e:
        QMessageBox.critical(None, "Error", 
            "Missing required system components. Please ensure Microsoft Visual C++ "
            "Redistributable is installed and try again.\n\nError: " + str(e))
        sys.exit(1)
    except Exception as e:
        QMessageBox.critical(None, "Error", 
            "An unexpected error occurred:\n\n" + str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()