# Employee Duty Schedule Parser

## Description

A Python script to parse employee duty schedules from HTML extracted from IVU (a roster generator), generate detailed shift reports, and export them to a structured text file with statistics, including:

- Total days parsed
- Breakdown of shifts by destination
- Breakdown of rest days by type
- Count of overnight shifts
- Timestamp of when the report was generated

## Requirements

- Python 3.x
- Required Python libraries:
  - `BeautifulSoup` (for HTML parsing)
  - `re` (for regular expressions)
  - `datetime` (for timestamp generation)

You can install the required libraries using `pip`:

`pip install beautifulsoup4`

## How to Use

### Step 1: Extract the HTML file
Before using the script, you need to extract the untitled.html file from the IVU duties personal page. This file should contain the employee duty roster in HTML format.

### Step 2: Prepare the Python Script
Download or clone the repository and ensure the Python script (parse_schedule.py) is in the same folder as the untitled.html file.

### Step 3: Run the Script
Run the following command in your terminal:

python parse_schedule.py

### Step 4: Input the File
The script will automatically read the untitled.html file from the same directory, parse it, and generate a text file with the parsed schedule.

Note: If your untitled.html file is named differently or located in another directory, you can specify the file path in the script.

### Example Output File Name
The script will generate a report in the following format:


`John_Doe_123456_duties_from_01_01_2024_to_10_01_2024.txt`


This file will contain the following sections:

- Statistics: Including total days parsed, total shifts, and rest days breakdown.
- Schedule: A detailed table showing each parsed date, duty, start time, and end time.
- Timestamp: The timestamp of when the report was generated (at the bottom).

