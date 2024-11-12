# gui/worker.py

from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd
from processing.processor import process_files  

class WorkerThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    results_ready = pyqtSignal(pd.DataFrame)  

    def __init__(self, product_type_path, sample_file_path, use_previous, categorized_df):
        super().__init__()
        self.product_type_path = product_type_path
        self.sample_file_path = sample_file_path
        self.use_previous = use_previous
        self.categorized_df = categorized_df  

    def run(self):
        try:
            # Call the updated process_files function
            results_df = process_files(
                product_type_path=self.product_type_path,
                sample_file_path=self.sample_file_path,
                use_previous=self.use_previous,
                categorized_df=self.categorized_df  # Pass the in-memory DataFrame
            )
            # Emit progress
            self.progress.emit("Processing completed successfully.")
            # Emit the processed results DataFrame
            self.results_ready.emit(results_df)
            # Emit finished signal
            self.finished.emit("Processing completed successfully.")
        except Exception as e:
            self.error.emit(str(e))
