# processing/processor.py

import os
import pandas as pd
import time
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from openai import OpenAI

from utils.helpers import clean_text, remove_null

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'keys.env')

load_dotenv(CONFIG_PATH)

def extract_product_info(text):
    """Extract product information using OpenAI API."""
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
    """Categorize products using OpenAI API."""
    client = OpenAI(
        api_key=os.getenv("API"),
        base_url="https://api.groq.com/openai/v1"
    )
    
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
            model="llama-3.1-8b-instant",
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
    """Splits the product list into batches of specified size."""
    return [product_list[i:i + batch_size] for i in range(0, len(product_list), batch_size)]

def categorize_products(product_list):
    """
    Categorizes all products, ensuring that every product is assigned a category.
    Reprocesses uncategorized products until all are categorized.
    Returns a pandas DataFrame with products and their assigned categories.
    """
    categorized_products = {}
    remaining_products = [product[0] for product in product_list if product[0]]

    iteration = 1
    max_iterations = 4  # To prevent infinite loops
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
    """Finds the category based on keywords in the LLM output."""
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
    """Finds the product based on keywords in the LLM output."""
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
    """Extracts the category for a given product title using OpenAI API."""
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
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error processing: {e}")
        return "Unknown"

def get_similar_products(category, product_title, df):
    """Finds similar products within the same category using OpenAI API."""
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
            model="llama-3.1-8b-instant",
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

def process_files(product_type_path, sample_file_path, use_previous, categorized_df):
    """
    Main processing function to categorize and match products.

    Args:
        product_type_path (str): Path to the Product Type Excel file.
        sample_file_path (str): Path to the Sample Excel file.
        use_previous (bool): Flag to use existing categorized DataFrame.
        categorized_df (pd.DataFrame or None): Existing categorized DataFrame.

    Returns:
        pd.DataFrame: Processed results DataFrame.
    """
    # Step 1: Categorize products or use existing categories
    if use_previous:
        if categorized_df is not None:
            print("Using existing categorized DataFrame.")
            df = categorized_df.copy()
        else:
            raise ValueError("No existing categorized data available.")
    else:
        print(f"Categorizing products from '{product_type_path}'.")
        try:
            product_df = pd.read_excel(product_type_path, header=None)
            product_list = product_df.values.tolist()
        except Exception as e:
            print(f"Error loading '{product_type_path}': {str(e)}")
            raise e

        # Categorize products
        df = categorize_products(product_list)
        print("Categorization complete.")

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
            'Product Title': generated_title,
            'Product Type': matched_product
        })

    results_df = pd.DataFrame(results)

    print(f"Processing complete. Ready to download results.")

    return results_df