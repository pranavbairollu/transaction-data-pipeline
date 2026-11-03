# Transaction Data Pipeline

A Python-based data processing project that reads transaction records from a CSV file, validates and cleans the data, detects duplicate and conflicting transactions, and generates company-wise summary reports.

The project demonstrates fundamental Data Engineering concepts such as data validation, data cleaning, aggregation, logging, and record reconciliation.

## Features

- Reads transaction records from CSV files using Python's `csv.DictReader`.
- Validates required columns and checks for missing or malformed records.
- Cleans transaction IDs and company names by removing unnecessary whitespace.
- Uses case-insensitive matching to normalize transaction IDs and company names.
- Validates transaction amounts using Python's `Decimal` for accurate financial calculations.
- Detects exact duplicate transactions.
- Identifies conflicting transaction IDs and excludes affected records from the final report.
- Calculates company-wise transaction totals, counts, and averages.
- Uses logging to track pipeline events, warnings, and errors.
- Performs record reconciliation to ensure all input records are accounted for.
- Generates a company-wise summary report in CSV format.

## Project Structure

```text
transaction-data-pipeline/
│
├── read_csv.py          # Main data processing pipeline
├── transactions.csv     # Input transaction data
├── company_report.csv   # Generated company-wise summary
└── README.md            # Project documentation
```

## Requirements

- Python 3.10 or later
- No external Python packages required.

### Python libraries used

- `csv` — Reading and writing CSV files.
- `pathlib` — Handling file paths.
- `decimal` — Accurate financial calculations.
- `logging` — Tracking pipeline events, warnings, and errors.

## How to Run

1. Clone or download this repository.
2. Make sure Python is installed.
3. Open a terminal in the project directory.
4. Run the pipeline:

```bash
python read_csv.py
```

The pipeline will:
- Read transactions from `transactions.csv`.
- Validate and process the records.
- Calculate company-wise summaries.
- Display the results in the terminal.
- Generate `company_report.csv` in the project directory.

## Sample Output

For the sample transaction data, the pipeline generates a company-wise summary:

| Company | Total | Count | Average |
|---|---:|---:|---:|
| Amazon | 150.00 | 2 | 75.00 |
| Flipkart | 200.00 | 1 | 200.00 |

The pipeline also displays record validation statistics and reconciliation results in the terminal.

The generated `company_report.csv` contains the company-wise summary.

## Data Quality Handling

The pipeline handles different data-quality issues:

| Issue | Handling |
|---|---|
| Missing required columns | Stops processing with an error |
| Missing or malformed CSV fields | Skips structurally invalid records |
| Empty transaction IDs | Rejects the record |
| Empty company names | Rejects the record |
| Invalid or negative amounts | Rejects the record |
| Exact duplicate transaction IDs | Counts repeated identical transactions and includes the transaction only once, provided the ID has no conflicting records |
| Conflicting transaction IDs | Excludes all valid records associated with the conflicting ID from the final report |
| Unaccounted records | Detected through record reconciliation |

This helps maintain data accuracy and ensures that every input record is accounted for.

## Learning Outcomes

Through this project, I practised:

- Reading and processing CSV files using Python.
- Working with dictionaries, sets, and functions.
- Handling exceptions and invalid data.
- Validating and cleaning incoming records.
- Using `Decimal` for financial calculations.
- Detecting duplicate and conflicting records.
- Performing data aggregation and reconciliation.
- Using logging to monitor data-processing operations.
- Generating structured CSV reports.

## Future Improvements

- Add automated unit tests.
- Support larger datasets efficiently.
- Introduce database integration.
- Build an automated ETL workflow.