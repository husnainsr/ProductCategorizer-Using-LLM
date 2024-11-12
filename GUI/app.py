# gui/app.py

import os
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox, QCheckBox, QSizePolicy
)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt

from .worker import WorkerThread  # Ensure WorkerThread is correctly imported

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Product Categorizer'
        self.left = 100
        self.top = 100
        self.width = 800
        self.height = 600

        # Initialize file paths with absolute paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.product_type_path = ""
        self.sample_file_path = ""
        self.output_path = os.path.join(self.base_dir, 'processed_output.xlsx')

        # In-Memory Storage for Categorized Products and Results
        self.categorized_df = None
        self.results_df = None

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Set a professional color scheme
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))  # Light gray background
        palette.setColor(QPalette.WindowText, Qt.black)
        self.setPalette(palette)

        # Fonts
        label_font = QFont('Arial', 12)
        button_font = QFont('Arial', 10, QFont.Bold)

        # Layouts
        main_layout = QVBoxLayout()

        # Product Type File Selection
        pt_layout = QHBoxLayout()
        pt_label = QLabel("Product Type File:")
        pt_label.setFont(label_font)
        self.pt_path_label = QLabel("No file selected")
        self.pt_path_label.setFont(label_font)
        self.pt_path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.pt_browse_btn = QPushButton("Browse")
        self.pt_browse_btn.setFont(button_font)
        self.pt_browse_btn.clicked.connect(self.browse_product_type)
        pt_layout.addWidget(pt_label, stretch=1)
        pt_layout.addWidget(self.pt_path_label, stretch=3)
        pt_layout.addWidget(self.pt_browse_btn, stretch=1)
        main_layout.addLayout(pt_layout)

        # Sample File Selection
        sample_layout = QHBoxLayout()
        sample_label = QLabel("Sample File:")
        sample_label.setFont(label_font)
        self.sample_path_label = QLabel("No file selected")
        self.sample_path_label.setFont(label_font)
        self.sample_path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.sample_browse_btn = QPushButton("Browse")
        self.sample_browse_btn.setFont(button_font)
        self.sample_browse_btn.clicked.connect(self.browse_sample_file)
        sample_layout.addWidget(sample_label, stretch=1)
        sample_layout.addWidget(self.sample_path_label, stretch=3)
        sample_layout.addWidget(self.sample_browse_btn, stretch=1)
        main_layout.addLayout(sample_layout)

        # Process Button
        self.process_btn = QPushButton("Process")
        self.process_btn.setFont(QFont('Arial', 12, QFont.Bold))
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                padding: 10px; 
                border: none; 
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.process_btn.clicked.connect(self.process_files)
        main_layout.addWidget(self.process_btn)

        # Download Button
        self.download_btn = QPushButton("Download Output")
        self.download_btn.setFont(QFont('Arial', 12, QFont.Bold))
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #008CBA; 
                color: white; 
                padding: 10px; 
                border: none; 
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #007bb5;
            }
        """)
        self.download_btn.clicked.connect(self.download_output)
        self.download_btn.setEnabled(False)
        main_layout.addWidget(self.download_btn)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setFont(QFont('Arial', 10))
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)
        self.show()

    def browse_product_type(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Product Type Excel File", "",
                                                  "Excel Files (*.xlsx *.xls)", options=options)
        if fileName:
            self.product_type_path = os.path.abspath(fileName)
            self.pt_path_label.setText(os.path.basename(fileName))

    def browse_sample_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Sample Excel File", "",
                                                  "Excel Files (*.xlsx *.xls)", options=options)
        if fileName:
            self.sample_file_path = os.path.abspath(fileName)
            self.sample_path_label.setText(os.path.basename(fileName))

    def process_files(self):
        if self.product_type_path and not self.categorized_df:
            # User has uploaded a Product Type file and categorized_df is not set
            use_previous = False
        elif self.categorized_df and self.sample_file_path:
            # User wants to process a Sample file using existing categorized_df
            use_previous = True
        elif self.product_type_path and self.categorized_df:
            # User wants to re-categorize with a new Product Type file
            reply = QMessageBox.question(
                self, 'Confirm Overwrite',
                "Uploading a new Product Type file will overwrite existing categorized data. Continue?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                use_previous = False
            else:
                return
        else:
            QMessageBox.critical(self, "Error", "Please select the appropriate files.")
            return

        self.process_btn.setEnabled(False)
        self.status_label.setText("Processing... Please wait.")
        self.worker = WorkerThread(
            self.product_type_path,
            self.sample_file_path,
            use_previous,
            self.categorized_df  # Pass the in-memory DataFrame
        )
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.processing_finished)
        self.worker.error.connect(self.processing_error)
        self.worker.results_ready.connect(self.update_results_df)  # Connect the new signal
        self.worker.start()

    def update_status(self, message):
        self.status_label.setText(message)

    def processing_finished(self, message):
        self.status_label.setText(message)
        self.process_btn.setEnabled(True)
        self.download_btn.setEnabled(True)
        QMessageBox.information(self, "Success", message)

    def processing_error(self, error_message):
        self.status_label.setText("Error occurred during processing.")
        self.process_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", error_message)

    def update_results_df(self, results_df):
        """
        Slot to receive the processed results DataFrame from the worker thread.
        """
        self.results_df = results_df
        print("Processed DataFrame updated in memory.")

    def download_output(self):
        if self.results_df is None:
            QMessageBox.critical(self, "Error", "No processed results available to download.")
            return

        options = QFileDialog.Options()
        savePath, _ = QFileDialog.getSaveFileName(self, "Save Output File", "processed_output.xlsx",
                                                  "Excel Files (*.xlsx *.xls)", options=options)
        if savePath:
            try:
                self.results_df.to_excel(os.path.abspath(savePath), index=False)
                QMessageBox.information(self, "Success", f"File saved to {savePath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
