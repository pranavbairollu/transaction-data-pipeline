# Transaction Data Pipeline

A Python-based data processing pipeline that reads transaction records from CSV files, validates and cleans incoming data, detects duplicate and conflicting transactions, performs company-wise aggregation, and generates structured CSV reports.

This project demonstrates practical Data Engineering concepts such as CSV ingestion, data validation, data quality checks, error handling, logging, aggregation, automated testing, and record reconciliation.

## Features

- **CSV Ingestion:** Reads transaction records using Python's `csv.DictReader`.
- **Schema Validation:** Validates required columns and detects missing or duplicate CSV headers.
- **Structural Validation:** Detects records with missing or extra fields.
- **Data Cleaning:** Removes unnecessary whitespace and normalizes transaction IDs and company names.
- **Transaction Validation:** Validates transaction IDs, company names, and transaction amounts.
- **Financial Accuracy:** Uses Python's `Decimal` for accurate financial calculations.
- **Duplicate Detection:** Identifies exact duplicate transactions.
- **Conflict Detection:** Identifies conflicting transaction IDs and excludes affected records from the final report.
- **Data Aggregation:** Calculates company-wise transaction totals, counts, and averages.
- **Logging and Error Handling:** Tracks pipeline events, warnings, CSV parsing errors, and report-writing failures.
- **Record Reconciliation:** Ensures every received record is accounted for before generating the final report.
- **CSV Report Generation:** Exports company-wise summary reports in CSV format.
- **Automated Testing:** Includes 30 unit tests covering valid records, invalid data, duplicates, conflicts, malformed CSV files, reconciliation failures, and report-writing failures.

## Project Structure

```text
transaction-data-pipeline/
│
├── read_csv.py              # Main data processing pipeline
├── transactions.csv         # Input transaction data
├── company_report.csv       # Generated company-wise report
├── README.md                # Project documentation
├── .gitignore               # Git ignored files and directories
│
└── tests/
    └── test_pipeline.py     # Automated unit tests
```

## Requirements

- Python 3.10 or later
- No external Python packages required.

### Python Standard Libraries Used

| Library | Purpose |
|---|---|
| `csv` | Reading and writing CSV files |
| `pathlib` | Handling file paths |
| `decimal` | Accurate financial calculations |
| `logging` | Tracking pipeline events and errors |
| `unittest` | Automated unit testing |

## How to Run

1. Clone the repository:

```bash
git clone https://github.com/pranavbairollu/transaction-data-pipeline.git
```

2. Navigate into the project directory:

```bash
cd transaction-data-pipeline
```

3. Run the pipeline:

```bash
python read_csv.py
```

The pipeline will:

- Read transactions from `transactions.csv`.
- Validate and process incoming records.
- Detect duplicates and conflicting transactions.
- Calculate company-wise summaries.
- Perform record reconciliation.
- Display processing statistics in the terminal.
- Generate `company_report.csv`.

## Running Tests

The project uses Python's built-in `unittest` framework.

Run the complete test suite using:

```bash
python -m unittest discover -s tests -v
```

### Test Coverage

The automated tests cover:

- Valid transaction processing.
- Invalid transaction IDs and company names.
- Invalid, negative, and non-finite amounts.
- Zero-value transactions.
- Duplicate and conflicting transaction IDs.
- Missing and extra CSV fields.
- Duplicate and missing CSV headers.
- Malformed CSV syntax.
- Record reconciliation.
- Report generation and report-writing failures.

**Current test status:** 30 tests passing.

## Sample Output

For the sample transaction data, the pipeline generates the following company-wise summary:

| Company | Total | Count | Average |
|---|---:|---:|---:|
| Amazon | 150.00 | 2 | 75.00 |
| Flipkart | 200.00 | 1 | 200.00 |

The pipeline also displays record validation statistics, duplicate information, rejected records, and reconciliation results in the terminal.

The generated `company_report.csv` contains the company-wise summary.

## Data Quality Handling

The pipeline handles different data-quality issues:

| Issue | Handling |
|---|---|
| Missing required columns | Stops processing with an error |
| Duplicate CSV headers | Stops processing with an error |
| Missing or extra CSV fields | Rejects structurally invalid records |
| Malformed CSV syntax | Stops processing with an error |
| Empty transaction IDs | Rejects the record |
| Empty company names | Rejects the record |
| Invalid or negative amounts | Rejects the record |
| Non-finite amounts | Rejects the record |
| Zero-value amounts | Accepted as valid |
| Exact duplicate transactions | Counts repeated identical transactions and includes the transaction only once if its ID has no conflict |
| Conflicting transaction IDs | Excludes all valid records associated with the conflicting ID |
| Reconciliation failures | Stops report generation |

Record reconciliation ensures that every received record is accounted for through validation rejections, post-validation exclusions, or valid transactions.

## Learning Outcomes

Through this project, I gained practical experience with:

- Reading and processing CSV files using Python.
- Working with dictionaries, lists, sets, and functions.
- Implementing data validation and cleaning.
- Handling exceptions and malformed input.
- Using `Decimal` for financial calculations.
- Detecting duplicate and conflicting records.
- Performing data aggregation.
- Implementing logging and error handling.
- Building record reconciliation checks.
- Writing automated unit tests using `unittest`.
- Organizing Python code into reusable functions.
- Working with Git and GitHub for version control.

## Future Improvements

- Support larger datasets efficiently.
- Introduce database integration using SQL.
- Add structured configuration management.
- Implement automated ETL workflows.
- Introduce CI/CD with automated test execution.
