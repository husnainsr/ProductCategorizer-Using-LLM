import sys
import os
import pandas as pd
import time
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog,
    QVBoxLayout, QHBoxLayout, QMessageBox, QCheckBox
)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from openai import OpenAI
from dotenv import load_dotenv
from fuzzywuzzy import fuzz



load_dotenv("keys.env")

def clean_text(text):
    # Remove HTML tags if present
    clean = re.sub('<[^<]+?>', '', text)
    return clean.strip()


def remove_null(text):
    if isinstance(text, str):
        text_lower = text.lower()
        remove_terms = ['null', 'mo', 'moi']
        parts = [part.strip() for part in text.split(',')]
        parts = [part for part in parts if part and 
                part.lower() not in remove_terms and 
                len(part.strip()) > 1]  # Ensure part has meaningful content
        
        return ', '.join(parts)
    return text


def extract_product_info(text):
    client = OpenAI(
        api_key=os.getenv("API"),
        base_url="https://api.groq.com/openai/v1"
    )
    
    system_prompt = """
    Extract product information and return ONLY a single line following this exact format:
    [product type], MODECAR, [car make], [car model], [year range], [additional information], [part number]

    Rules:
    - Return ONLY the formatted string, no explanations or additional text
    - Product name in small letters
    - MODECAR always in capitals
    - Use "null" for any missing information
    - Years must be in YYYY-YYYY format
    - Always include all 7 parts separated by commas

    Create a concise product title from the following description, strictly according to this format:
    '[product type], MODECAR, [car make], [car model], [year range], [additional information], [part number]'.

    If any part of the information is not available in the description, ignore that. Only provide the product title in the specified format, with no extra information or explanations.

    """
    
    prompt = f"{system_prompt}\n\nText to process:\n{text}"
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        final_response = remove_null(response.choices[0].message.content.strip())
        return final_response
    except Exception as e:
        return f"Error occurred: {str(e)}"
    

def extract_product_categories(product_list):
    client = OpenAI(
        api_key=os.getenv("API"),
        base_url="https://api.groq.com/openai/v1"  # Ensure this is the correct base URL
    )
    
    # Prepare the system prompt with strict formatting instructions
    system_prompt = f"""
Ești un expert în categorisirea pieselor auto. Sarcina ta este să clasifici fiecare produs auto din lista de mai jos
în una dintre următoarele categorii, pe baza funcției sale sau a asocierii cu anumite sisteme ale vehiculului.

Categorii:
1. **Sistem de frânare**
2. **Suspensie și direcție**
3. **Componente motor**
4. **Transmisie și ambreiaj**
5. **Sistem de răcire și încălzire**
6. **Sistem electric și senzori**
7. **Caroserie și interior**
8. **Sistem de combustibil și emisii**
9. **Sistem de evacuare**
10. **Diverse**

**Instrucțiuni:**
- Răspunde doar cu perechi de `Produs: Categorie`.
- Fiecare pereche trebuie să fie pe o linie separată.
- Nu include numere, titluri, sau alte texte suplimentare.
- Exemple: Disc frână: Sistem de frânare Amortizor: Suspensie și direcție

**Produse:**
{product_list}

**Formatul răspunsului trebuie să fie exact:**

"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Replace with the correct model identifier if different
            messages=[{"role": "user", "content": system_prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error occurred during API call: {str(e)}")
        return ""


def parse_llm_response(response_text):
    """
    Parses the LLM response and returns a dictionary of product-category pairs.
    Expected format: 'Produs: Categorie' per line.
    """
    categorized = {}
    lines = response_text.split('\n')
    for line_number, line in enumerate(lines, start=1):
        if ':' in line:
            try:
                product, category = line.split(':', 1)
                product = product.strip().lstrip('-').strip()
                category = category.strip()
                # Validate category
                valid_categories = [
                    "Sistem de frânare",
                    "Suspensie și direcție",
                    "Componente motor",
                    "Transmisie și ambreiaj",
                    "Sistem de răcire și încălzire",
                    "Sistem electric și senzori",
                    "Caroserie și interior",
                    "Sistem de combustibil și emisii",
                    "Sistem de evacuare",
                    "Diverse"
                ]
                if category not in valid_categories:
                    print(f"Line {line_number}: Invalid category '{category}' for product '{product}'. Skipping.")
                    continue
                if product and category:
                    categorized[product] = category
                else:
                    print(f"Line {line_number}: Incomplete data. Skipping.")
            except ValueError:
                print(f"Line {line_number}: Unable to split line. Skipping.")
                continue  # Skip lines that don't match the expected format
        else:
            print(f"Line {line_number}: No ':' found in line. Skipping.")
    return categorized


def convert_to_batches(product_list, batch_size=50):
    """
    Splits the product list into batches of specified size.
    """
    return [product_list[i:i + batch_size] for i in range(0, len(product_list), batch_size)]


def categorize_products(product_list):
    """
    Categorizes all products, ensuring that every product is assigned a category.
    Reprocesses uncategorized products until all are categorized.
    Returns a pandas DataFrame with products and their assigned categories.
    """
    # Initialize dictionary to store results
    categorized_products = {}
    # Flatten the product list (assuming product_list is a list of lists)
    remaining_products = [product[0] for product in product_list if product[0]]

    iteration = 1
    max_iterations = 3  # To prevent infinite loops
    while remaining_products and iteration <= max_iterations:
        batches = convert_to_batches(remaining_products, batch_size=50)
        new_remaining = []

        for i, batch in enumerate(batches, start=1):
            # Convert batch list to a string formatted for the prompt
            batch_str = '\n'.join([f"- {product}" for product in batch])
            response = extract_product_categories(batch_str)
            
            if not response:
                new_remaining.extend(batch)
                time.sleep(2)  # Wait before retrying
                continue

            categorized = parse_llm_response(response)
            for product in batch:
                if product in categorized and categorized[product]:
                    categorized_products[product] = categorized[product]
                else:
                    new_remaining.append(product)
            

        if new_remaining == remaining_products:
            break

        remaining_products = new_remaining
        if remaining_products:
            iteration += 1
            time.sleep(2)  # Wait before next iteration to avoid rate limits

    # Convert the dictionary to a DataFrame
    df = pd.DataFrame(list(categorized_products.items()), columns=['Product', 'Category'])
    return df

def find_category_by_keywords(llm_output, categories):
    # Convert LLM output to lowercase for case-insensitive matching
    llm_output = llm_output.lower()
    
    # Create a dictionary of categories and their lowercase versions
    category_keywords = {cat.lower(): cat for cat in categories}
    
    # Check if any category word appears in the LLM output
    for keyword, original_category in category_keywords.items():
        if keyword in llm_output:
            return original_category
    
    return None


def find_product_by_keywords(llm_output, category_products):
    # Convert LLM output and products to lowercase for case-insensitive matching
    llm_output = llm_output.lower()
    
    # Create a dictionary of products and their lowercase versions
    product_keywords = {prod.lower(): prod for prod in category_products}
    
    # First try exact matching
    for keyword, original_product in product_keywords.items():
        if keyword in llm_output:
            return original_product
    
    # If no exact match, try fuzzy matching
    # Split LLM output into words
    llm_words = llm_output.split()
    
    best_match = None
    highest_ratio = 0
    
    # Compare each word against each product
    for word in llm_words:
        for keyword, original_product in product_keywords.items():
            ratio = fuzz.ratio(word, keyword)
            if ratio > highest_ratio and ratio > 80:  # 80% similarity threshold
                highest_ratio = ratio
                best_match = original_product
    
    return best_match if best_match else None


def extract_category_for_product(product_title, categories):
    client = OpenAI(
        api_key=os.getenv("API2"),
        base_url="https://api.groq.com/openai/v1"
    )
    
    prompt = f"""
    Given the following product title, determine which category it belongs to.
    Product: {product_title}
    
    Respond with only the category name from the following options:
    {', '.join(categories)}
    """
    
    try:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error processing: {e}")
        return "Unknown"
    
def get_similar_products(category, product_title, df):
    # Get all products from the same category
    category_products = df[df['Category'] == category]['Product'].tolist()
    
    client = OpenAI(
        api_key=os.getenv("API2"),
        base_url="https://api.groq.com/openai/v1"
    )
    
    prompt = f"""
    Given the following product: {product_title}
    And these similar products from the same category:
    {', '.join(category_products)}
    
    Return exactly ONE product from the list that most closely matches the given product.
    Respond with only the product name, nothing else.
    """
    
    try:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100
        )
        llm_output = response.choices[0].message.content.strip()
        
        # Try to find exact product match from LLM output
        matched_product = find_product_by_keywords(llm_output, category_products)
        if matched_product:
            return matched_product
        else:
            print(f"No exact product match found in LLM output: {llm_output}")
            return "No match found"
            
    except Exception as e:
        print(f"Error processing similar products: {e}")
        return "Error in processing"
    


def process_files(product_type_path, sample_file_path, use_previous, previous_categorized_path, output_path):
    # Step 1: Check if 'categorized_products.xlsx' exists
    if use_previous:
        if os.path.exists(previous_categorized_path):
            print(f"'{previous_categorized_path}' exists. Loading categorized products.")
            try:
                df = pd.read_excel(previous_categorized_path)
            except Exception as e:
                print(f"Error loading '{previous_categorized_path}': {str(e)}")
                raise e
        else:
            raise FileNotFoundError(f"Previous categorized file '{previous_categorized_path}' not found.")
    else:
        print(f"'{previous_categorized_path}' does not exist or not using previous file. Categorizing products from '{product_type_path}'.")
        try:
            product_df = pd.read_excel(product_type_path, header=None)
            product_list = product_df.values.tolist()
        except Exception as e:
            print(f"Error loading '{product_type_path}': {str(e)}")
            raise e
        
        # Categorize products
        final_df = categorize_products(product_list)
        
        # Save the result to a new Excel file
        try:
            final_df.to_excel(previous_categorized_path, index=False)
            print(f"Categorization complete. Results saved to '{previous_categorized_path}'.")
        except Exception as e:
            print(f"Error saving the results: {str(e)}")
            raise e

        df = final_df  # Use the newly created dataframe

    # Step 2: Read sample file into sample_df
    try:
        sample_df = pd.read_excel(sample_file_path, header=None)
    except Exception as e:
        print(f"Error loading '{sample_file_path}': {str(e)}")
        raise e

    # Proceed with processing using 'df' and 'sample_df'
    # Get unique categories from 'df'
    categories = df['Category'].unique()

    results = []
    for index, row in sample_df.iterrows():
        product_title = row[0]

        # Generate a clean product title
        clean_title = clean_text(product_title)
        generated_title = extract_product_info(clean_title)

        # First get LLM output for category
        llm_category = extract_category_for_product(product_title, categories)
        
        # Then try keyword matching on LLM output
        category = find_category_by_keywords(llm_category, categories)
        
        if category is not None:
            print(f"Category found by keyword matching: {category}")
            # Get similar product from the category
            matched_product = get_similar_products(category, product_title, df)
            print(f"Matched product: {matched_product}")
        else:
            print(f"No matching category found in LLM output: {llm_category}")
            category = "Unknown"
            matched_product = "No match found"
        
        results.append({
            # 'Product': product_title, 
            'product title': generated_title,
            # 'Category': category,
            'product type': matched_product
        })

    # Create a new DataFrame with results
    results_df = pd.DataFrame(results)
    # Save results to Excel
    try:
        results_df.to_excel(output_path, index=False)
        print(f"Processing complete. Results saved to '{output_path}'.")
    except Exception as e:
        print(f"Error saving the results: {str(e)}")
        raise e



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
        self.previous_categorized_path = "categorized_products.xlsx"
        self.output_path = "processed_output.xlsx"

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
        self.pt_browse_btn = QPushButton("Browse")
        self.pt_browse_btn.setFont(button_font)
        self.pt_browse_btn.clicked.connect(self.browse_product_type)
        self.use_prev_checkbox = QCheckBox("Use Previous Categorized File")
        self.use_prev_checkbox.setFont(label_font)
        pt_layout.addWidget(pt_label)
        pt_layout.addWidget(self.pt_path_label)
        pt_layout.addWidget(self.pt_browse_btn)
        pt_layout.addWidget(self.use_prev_checkbox)
        main_layout.addLayout(pt_layout)

        # Sample File Selection
        sample_layout = QHBoxLayout()
        sample_label = QLabel("Sample File:")
        sample_label.setFont(label_font)
        self.sample_path_label = QLabel("No file selected")
        self.sample_path_label.setFont(label_font)
        self.sample_browse_btn = QPushButton("Browse")
        self.sample_browse_btn.setFont(button_font)
        self.sample_browse_btn.clicked.connect(self.browse_sample_file)
        sample_layout.addWidget(sample_label)
        sample_layout.addWidget(self.sample_path_label)
        sample_layout.addWidget(self.sample_browse_btn)
        main_layout.addLayout(sample_layout)

        # Process Button
        self.process_btn = QPushButton("Process")
        self.process_btn.setFont(QFont('Arial', 12, QFont.Bold))
        self.process_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.process_btn.clicked.connect(self.process_files)
        main_layout.addWidget(self.process_btn)

        # Download Button
        self.download_btn = QPushButton("Download Output")
        self.download_btn.setFont(QFont('Arial', 12, QFont.Bold))
        self.download_btn.setStyleSheet("background-color: #008CBA; color: white; padding: 10px;")
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
                pd.read_excel(self.output_path).to_excel(savePath, index=False)
                QMessageBox.information(self, "Success", f"File saved to {savePath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

# ------------------ Main Execution ------------------

def main():
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()


