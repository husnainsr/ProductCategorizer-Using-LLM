# gui/app.py

import os
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox, QCheckBox, QSizePolicy
)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt

from worker import WorkerThread

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Product Categorizer'
        self.left = 100
        self.top = 100
        self.width = 800
        self.height = 600

        # Initialize file paths
        self.product_type_path = ""
        self.sample_file_path = ""
        self.previous_categorized_path = os.path.join(os.path.dirname(__file__), '../categorized_products.xlsx')
        self.output_path = os.path.join(os.path.dirname(__file__), '../processed_output.xlsx')

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
        self.use_prev_checkbox = QCheckBox("Use Previous Categorized File")
        self.use_prev_checkbox.setFont(label_font)
        pt_layout.addWidget(pt_label, stretch=1)
        pt_layout.addWidget(self.pt_path_label, stretch=3)
        pt_layout.addWidget(self.pt_browse_btn, stretch=1)
        pt_layout.addWidget(self.use_prev_checkbox, stretch=2)
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
            self.product_type_path = fileName
            self.pt_path_label.setText(os.path.basename(fileName))
            if self.use_prev_checkbox.isChecked():
                self.use_prev_checkbox.setChecked(False)  # Uncheck if a new file is selected

    def browse_sample_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Sample Excel File", "",
                                                  "Excel Files (*.xlsx *.xls)", options=options)
        if fileName:
            self.sample_file_path = fileName
            self.sample_path_label.setText(os.path.basename(fileName))

    def process_files(self):
        use_previous = self.use_prev_checkbox.isChecked()
        if use_previous:
            if not os.path.exists(self.previous_categorized_path):
                QMessageBox.critical(self, "Error", f"Previous categorized file '{self.previous_categorized_path}' not found.")
                return
            if not self.sample_file_path:
                QMessageBox.critical(self, "Error", "Please select a sample file.")
                return
        else:
            if not self.product_type_path or not self.sample_file_path:
                QMessageBox.critical(self, "Error", "Please select both product type and sample files.")
                return

        self.process_btn.setEnabled(False)
        self.status_label.setText("Processing... Please wait.")
        self.worker = WorkerThread(
            self.product_type_path,
            self.sample_file_path,
            use_previous,
            self.previous_categorized_path,
            self.output_path
        )
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.processing_finished)
        self.worker.error.connect(self.processing_error)
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

    def download_output(self):
        options = QFileDialog.Options()
        savePath, _ = QFileDialog.getSaveFileName(self, "Save Output File", "processed_output.xlsx",
                                                  "Excel Files (*.xlsx *.xls)", options=options)
        if savePath:
            try:
                from pandas import read_excel
                df = read_excel(self.output_path)
                df.to_excel(savePath, index=False)
                QMessageBox.information(self, "Success", f"File saved to {savePath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
