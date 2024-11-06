# gui/worker.py

from PyQt5.QtCore import QThread, pyqtSignal
from processing.processor import process_files

class WorkerThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, product_type_path, sample_file_path, use_previous, previous_categorized_path, output_path):
        super().__init__()
        self.product_type_path = product_type_path
        self.sample_file_path = sample_file_path
        self.use_previous = use_previous
        self.previous_categorized_path = previous_categorized_path
        self.output_path = output_path

    def run(self):
        try:
            self.progress.emit("Starting processing...")
            process_files(
                self.product_type_path,
                self.sample_file_path,
                self.use_previous,
                self.previous_categorized_path,
                self.output_path
            )
            self.finished.emit("Processing completed successfully.")
        except Exception as e:
            self.error.emit(str(e))
