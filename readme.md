# ProductCategoizer



**ProductCategoizer** is a user-friendly desktop application designed to efficiently categorize and match products. Built with Python and PyQt5, this tool allows users to upload product type files, process sample files, and download the results seamlessly without the need for intermediate file storage.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
    - [1. Install Conda](#1-install-conda)
    - [2. Create a Conda Environment](#2-create-a-conda-environment)
    - [3. Activate the Environment](#3-activate-the-environment)
    - [4. Install Dependencies](#4-install-dependencies)
    - [5. Build the Executable](#5-build-the-executable)
    - [6. Configure Environment Variables](#6-configure-environment-variables)
- [Running the Application](#running-the-application)
  - [Using Python](#using-python)
    - [1. Activate the Conda Environment](#1-activate-the-conda-environment)
    - [2. Run the Application](#2-run-the-application)
  - [Using the Standalone Executable](#using-the-standalone-executable)
    - [1. Navigate to the `dist` Directory](#1-navigate-to-the-dist-directory)
    - [2. Run the Executable](#2-run-the-executable)
- [Usage](#usage)
  - [Processing Files](#processing-files)
    - [Upload Product Type File](#upload-product-type-file)
    - [Upload Sample File](#upload-sample-file)
    - [Process Files](#process-files)
  - [Downloading Results](#downloading-results)
    - [Save Processed Results](#save-processed-results)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Configuration](#configuration)
  - [API Keys and Environment Variables](#api-keys-and-environment-variables)
- [Error Handling](#error-handling)
- [License](#license)
- [Contact](#contact)

## Features

- **In-Memory Categorization:** Categorize products without reading from or writing to disk.
- **Intuitive GUI:** Built with PyQt5, offering a clean and professional user interface.
- **Efficient Processing:** Quickly process large Excel files to categorize and match products.
- **Downloadable Results:** Save processed results directly from the application without intermediate storage.
- **Robust Error Handling:** Provides clear error messages and logs for a seamless user experience.
- **Standalone Executable:** Easily distribute the application as a single executable file using PyInstaller.

## Getting Started

Follow these instructions to set up and run the ProductCategoizer application on your local machine.

### Prerequisites

- **Operating System:** Windows 10 or later
- **Python:** Version 3.7 or higher
- **Conda:** Recommended for managing virtual environments

### Installation

#### 1. Install Conda

**Conda** is a package, dependency, and environment management tool that helps manage different projects with varying dependencies.

**Steps to Install Conda:**

1. **Download Miniconda:**
   
   Miniconda is a minimal installer for Conda. It includes only Conda and its dependencies, making it lightweight.
   
   - Visit the [Miniconda Downloads](https://docs.conda.io/en/latest/miniconda.html) page.
   - Choose the appropriate installer for your Windows system (64-bit is recommended).
   - Download the `.exe` installer.

2. **Run the Installer:**
   
   - Locate the downloaded `Miniconda3-latest-Windows-x86_64.exe` file.
   - Double-click the installer to run it.
   - Follow the on-screen instructions:
     - **License Agreement:** Read and accept the terms.
     - **Installation Type:** Choose whether to install for "Just Me" or "All Users".
     - **Installation Directory:** Select the desired installation location.
     - **Advanced Options:**
       - It's recommended to add Conda to your PATH environment variable for easier access. However, if you're unsure, you can use the Anaconda Prompt which automatically sets up the environment.

3. **Verify Installation:**
   
   Open the Command Prompt and type:

   ``` plaintext
   conda --version
   ```

   You should see the Conda version installed, e.g., `conda 4.10.3`.

#### 2. Create a Conda Environment

Creating a dedicated environment helps manage dependencies without affecting other projects.

``` bash 
conda create --name productcategorizer python=3.11.7
```

#### 3. Activate the Environment

Activate the newly created environment to start using it.

``` bash 
conda activate productcategorizer
```

- Your command prompt should now show `(productcategorizer)` indicating the active environment.

#### 4. Install Dependencies

Install the required Python packages listed in `requirements.txt`.

``` bash 
pip install --upgrade pip
pip install -r requirements.txt
```

- **`pip install --upgrade pip`**: Upgrades `pip` to the latest version.
- **`pip install -r requirements.txt`**: Installs all dependencies listed in the `requirements.txt` file.

**Contents of `requirements.txt`:**

``` plaintext
PyQt5
pandas
openpyxl
python-dotenv
fuzzywuzzy
python-Levenshtein
xlrd
```

#### 5. Build the Executable

Use PyInstaller to create a standalone executable of the application.

``` bash
python -m PyInstaller --onefile --windowed --add-data "config/keys.env;config" main.py
```

- **`--onefile`**: Packages the application into a single executable.
- **`--windowed`**: Prevents a console window from appearing (suitable for GUI apps).
- **`--add-data "config/keys.env;config"`**: Includes the `keys.env` file in the `config` directory within the executable.

**Notes:**

- **Path Separators:** Use forward slashes (`/`) or double backslashes (`\\`) on Windows.
- **Additional Resources:** If you have other resources like stylesheets or icons, include them using additional `--add-data` flags.

**Example Including a Stylesheet and Icon:**

``` bash
python -m PyInstaller --onefile --windowed \
--add-data "config/keys.env;config" \
--add-data "resource/styles.qss;resource" \
--add-data "resource/icon.ico;resource" \
main.py
```

#### 6. Configure Environment Variables

The application uses a `keys.env` file to manage sensitive information like API keys.

1. **Locate the `keys.env` File:**

``` plaintext
ProductCategoizer/
├── config/
│   ├── keys.env
│   └── __init__.py
└───...
```


2. **Edit `keys.env`:**

- Open `config/keys.env` in a text editor (e.g., Notepad, VS Code).

- Add or modify the necessary keys. The format should be `KEY=VALUE`.

**Example `keys.env`:**

``` plaintext
OPENAI_API_KEY=your_openai_api_key_here
ANOTHER_API_KEY=your_other_api_key_here
```

- **Security Note:** Do not share or expose `keys.env` publicly to protect sensitive data.

3. **Save the File:**

- After adding the required keys, save and close the `keys.env` file.

## Running the Application

Once the environment is set up, dependencies are installed, and the executable is built, you can run the application.

### Using Python

If you prefer running the application directly via Python (useful for development or debugging):

#### 1. Activate the Conda Environment

``` bash
conda activate productcategorizer
```

#### 2. Run the Application

``` bash
python main.py
```

### Using the Standalone Executable

For a hassle-free experience without needing Python installed on the target machine:

#### 1. Navigate to the `dist` Directory

    ``` bash
cd dist
```

#### 2. Run the Executable

- **Double-Click:** Locate `main.exe` in the `dist` folder and double-click it to run.

- **Command Prompt:**

``` bash
.\main.exe
```

## Usage

### Processing Files

#### Upload Product Type File

1. Click the "Browse" button next to "Product Type File".
2. Select your Excel file containing the product types.
3. The selected file path will be displayed.

#### Upload Sample File

1. Click the "Browse" button next to "Sample File".
2. Select your Excel file containing the sample products.
3. The selected file path will be displayed.

#### Process Files

1. Click the "Process" button.
2. The application will categorize the products in-memory and process the sample file.
3. Upon successful processing, a success message will be displayed, and the "Download Output" button will be enabled.

### Downloading Results

#### Save Processed Results

1. Click the "Download Output" button.
2. Choose the desired location and filename for the output Excel file.
3. The processed results will be saved to the specified location.

## Project Structure

``` plaintext
ProductCategoizer/
├── .gitignore
├── categorized_products.xlsx
├── main.py
├── main.spec
├── processed_output.xlsx
├── requirements.txt
├── build/
│   └── main/
│       ├── Analysis-00.toc
│       ├── base_library.zip
│       ├── EXE-00.toc
│       ├── main.pkg
│       ├── PKG-00.toc
│       ├── PYZ-00.pyz
│       ├── PYZ-00.toc
│       ├── warn-main.txt
│       └── xref-main.html
├── config/
│   ├── keys.env
│   └── __init__.py
├── dist/
│   └── main.exe
├── gui/
│   ├── app.py
│   ├── worker.py
│   └── __init__.py
├── processing/
│   ├── processor.py
│   └── __init__.py
├── resource/
│   ├── __init__.py
│   ├── styles.qss
│   └── icon.ico
└── utils/
    ├── helpers.py
    └── __init__.py

```


- **`.gitignore`**: Specifies intentionally untracked files to ignore.
- **`categorized_products.xlsx`**: *(If still used for any purpose.)*
- **`main.py`**: Entry point of the application.
- **`main.spec`**: PyInstaller specification file.
- **`processed_output.xlsx`**: Stores the processed results.
- **`requirements.txt`**: Lists all Python dependencies.
- **`build/`**: Contains temporary build files generated by PyInstaller.
- **`config/`**: Stores configuration files such as `keys.env`.
- **`dist/`**: Contains the standalone executable (`main.exe`) generated by PyInstaller.
- **`gui/`**: Holds the GUI components (`app.py`, `worker.py`).
- **`processing/`**: Contains the core processing logic (`processor.py`).
- **`resource/`**: Stores resources like icons and stylesheets (`styles.qss`, `icon.ico`).
- **`utils/`**: Includes utility scripts (`helpers.py`).

## Dependencies

The application relies on the following Python packages:

- **PyQt5**: For building the graphical user interface.
- **pandas**: For data manipulation and analysis.
- **openpyxl**: For reading and writing Excel files.
- **python-dotenv**: For managing environment variables.
- **fuzzywuzzy** and **python-Levenshtein**: For string matching and categorization.
- **xlrd**: For reading Excel files.

All dependencies are listed in the `requirements.txt` file. To install them, run:

``` plaintext
pip install -r requirements.txt
```

## Configuration

### API Keys and Environment Variables

The `config/keys.env` file stores sensitive information like API keys. Ensure that this file is properly configured with the necessary keys before running the application.

**Steps to Configure `keys.env`:**

1. **Open `keys.env`:**

   - Navigate to the `config/` directory.
   - Open `keys.env` in a text editor (e.g., Notepad, VS Code).

2. **Add Your Keys:**

   - Use the format `KEY=VALUE` for each environment variable.
   
   **Example `keys.env`:**

    ``` plaintext
   API=your_groq_api_key_here
   API2=your_groq_api_key_here
   ```

3. **Save the File:**

   - After adding the required keys, save and close the `keys.env` file.

**Security Note:** Do not share or expose `keys.env` publicly to protect sensitive data. It's included in `.gitignore` to prevent accidental commits.

### Adjusting Settings

Modify any configuration settings as needed by editing the relevant files in the `config/` directory.

## Error Handling

The application is designed to handle errors gracefully and provide clear feedback to the user.

- **Missing Files:** If required files are not selected or found, the application will display an error message.
- **Invalid File Formats:** Uploading incorrectly formatted Excel files will prompt an error.
- **Processing Issues:** Any issues during processing will be logged and communicated to the user.

