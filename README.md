# Geo Photo Toolkit

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command-line toolkit for Geo Data Scientists, analysts, and researchers to streamline the processing of geotagged photos. This tool provides a powerful, repeatable workflow to extract geospatial metadata from images and generate rich, interactive map files (`.kmz`) with embedded photos for visualization and reporting.

Whether you're analyzing field survey data, documenting infrastructure, or conducting geographical research, this toolkit bridges the gap between your raw photos and actionable, map-based insights.

## Key Features

- **GPS Data Extraction**: Automatically scan a directory of images and extract critical EXIF metadata, including latitude, longitude, and timestamps.
- **Automated Path Inclusion**: Optionally include the full, absolute path to each source image in the output, creating a seamless pipeline.
- **Flexible Output**: Save extracted data into either `.xlsx` for spreadsheet analysis or `.csv` for use in other data pipelines.
- **Direct KMZ Generation**: Read a structured `.csv` file to produce a self-contained `.kmz` file, with photos embedded directly in the map points, ready for use in Google Earth, QGIS, or other GIS applications.
- **End-to-End Automation**: A fully automated two-step process to go from a folder of photos to a portable, interactive map file with zero manual data entry.
- **Configuration-Driven**: Customize default folder names and other settings.
- **Robust Logging**: All operations are logged to both the console and a file for full traceability and easy debugging.

## Installation and Setup

This project uses `uv` for fast and efficient project and environment management. You need to install `uv`, a small utility that will automatically download a private version of Python for the toolkit.

- **For Windows Users:**

  1. Click the Start Menu and type `PowerShell`.
  2. Open the **Windows PowerShell** application.
  3. Copy and paste the following command into the PowerShell window and press Enter:

        ```powershell
        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
        ```

- **For macOS or Linux Users:**

  1. Open the **Terminal** application.
  2. Copy and paste the following command into the Terminal window and press Enter:

        ```bash
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```

    Close and reopen your Terminal or PowerShell window after the installation is complete.

### Prerequisites

- Python 3.9 or newer. (installed via `uv`)
- `uv` installed on your system (read above).
- [Windows Terminal](https://apps.microsoft.com/detail/9n0dx20hk701?hl=en-US&gl=US) App (Optional on Windows)

### Step-by-Step Installation

1. **Clone the Repository**

    ```bash
    git clone https://github.com/parkisutama/geo-photo-toolkit
    cd geo-photo-toolkit
    ```

    or you can directly download this project :

   1. Navigate to the project's GitHub page.
   2. Click the green **`<> Code`** button near the top right.
   3. In the dropdown menu, click **Download ZIP**.
   4. Save the file to a memorable location, like your **Desktop** or **Documents** folder.
   5. Find the downloaded `.zip` file and **unzip** or **extract** it. You will now have a folder named something like `geo-photo-toolkit-main`. This is your main project folder.

2. **Create and Activate Virtual Environment**

    ```bash
    uv venv
    .venv\Scripts\activate
    # On macOS/Linux source .venv/bin/activate
    ```

3. **Install Dependencies**

Install the project and all its dependencies in editable mode.

> be careful of `.` after -e

```bash
    uv pip install -e .
```

## End-to-End Workflow (Example Scenario)

This toolkit is designed to make the journey from photos to map as simple as possible.

**Goal**: You are a field researcher with a folder of geotagged photos from various survey sites. Your goal is to create a single map file to share with stakeholders, where each point on the map shows the location and the photo taken there.

**Your files**: You have a folder at `C:\Users\You\Documents\field_photos\` containing all your `.jpg` images.

---

### **Step 1: Extract Data and Image Paths in a Single Command**

Run the `gps-extract` command using the `--include-full-path` flag. This is the key to automating the process. It tells the tool to include a column with the full path to each image in the output file.

```bash
python main.py gps-extract --input-dir "C:\Users\You\Documents\field_photos" --output-file "site_data.csv" --include-full-path
```

- **What it does**: The tool scans every image, extracts its GPS data, and creates a CSV file. Because you used `--include-full-path` flag, this CSV now contains a photo_path column with the full path to each source image.

- **Result**: It creates site_data.csv with a structure ready for the next step:

| name        | description  | file_name   | photo_path                                      |
|-------------|--------------|-------------|-------------------------------------------------|
| IMG_001.jpg | Timestamp... | IMG_001.jpg | C:\Users\You\Documents\field_photos\IMG_001.jpg |
| IMG_002.jpg | Timestamp... | IMG_002.jpg | C:\Users\You\Documents\field_photos\IMG_002.jpg |

> Change the .csv to .xlsx if you prefer an Excel file.

### Step 2: Generate the KMZ File Directly

Now, use the CSV or EXCEL file you just created as the direct input for the kmz-generate command. No manual editing of the CSV or EXCEL is required.

```bash
python main.py kmz-generate --input-file "site_data.csv" --output-dir "briefing_map"
```

- **What it does**: The tool reads each row from site_data.csv. It finds the photo_path column, locates each image on your computer, and packages it inside the final .kmz file.

- **Result**: It creates briefing_map/site_data_... .kmz. This is a fully portable file. You can send it to anyone, and when they open it in Google Earth or QGIS, they will see the points on the map and be able to click on them to see the embedded photos, regardless of whether they have the original image files.

> You can edit the csv before generating kmz file. Let say you need to give number and name of each foto. You can add it either in name column or description column. After information you want updated you can start generate .kmz file

### Command Reference

For more details on all available options, use the --help flag.

```bash
python main.py gps-extract --help
python main.py kmz-generate --help
```

## Advanced Usage: Configuration Files

For complete control over the data extraction and map generation, the toolkit uses a `config.toml` file. You can have a `global_config.toml` in the main folder for your default settings, and use the `--config` flag to point to a smaller, project-specific `.toml` file to override those defaults.

**Example `config.toml`:**

```toml
[extract.columns]
camera_model = "Model"
altitude = "GPSAltitude"
lat = "GPSLatitude"
lon = "GPSLongitude"

[kmz.description]
template = """
    <b>Model:</b> {camera_model}<br>
    <b>Altitude:</b> {altitude:.1f}m
"""
```

## Dependencies and Acknowledgements

This toolkit is made possible by the incredible work of developers in the open-source community. This toolkit is made possible by the incredible work of developers in the open-source community. We gratefully acknowledge the pivotal role of the following libraries:

- Typer: For making the creation of clean, powerful, and user-friendly command-line interfaces remarkably simple and enjoyable. Its design is a pleasure to work with.
Pydantic: For providing robust data validation and settings management through Python type hints. It brings confidence and clarity to the application's configuration.

- Pandas: The cornerstone of data manipulation in Python. Its powerful DataFrame object is indispensable for reading, organizing, and writing the tabular data that drives this toolkit.

- Pillow (PIL Fork): The essential library for opening, manipulating, and saving many different image file formats. The ability to access EXIF metadata is a core function of this toolkit, and Pillow makes it possible.
- simplekml: For providing an elegant and Pythonic way to generate KML files. It abstracts away the complexities of the KML standard, allowing us to focus on the data.
Requests: For making HTTP requests humane. It powers the file downloader with a simple and reliable API.

- Openpyxl: The go-to library for reading and writing Excel 2010+ files, enabling the .xlsx output feature.

- fuzzywuzzy & tlsh: These libraries are included in the analysis module to provide powerful capabilities for identifying duplicate and similar images by filename or by content.

A sincere thank you to the maintainers and contributors of these projects. Your dedication enables the creation of powerful and practical tools like this one.
