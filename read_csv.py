
import csv
from pathlib import Path
from decimal import Decimal, InvalidOperation
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


def aggregate_transactions(transactions, records_received):
    valid_transactions_by_id = {}
    conflicted_ids = set()
    conflicted_records = 0
    exact_duplicates = 0
    valid_records = 0
    invalid_id_records = 0
    invalid_record_types = 0
    invalid_company_records = 0
    invalid_amount_records = 0

    for transaction in transactions:

        if not isinstance(transaction, dict):
            invalid_record_types += 1
            continue

        transaction_id = transaction.get("transaction_id")

        if not isinstance(transaction_id, str):
            invalid_id_records += 1
            logging.warning("Skipping transaction with invalid ID")
            continue

        transaction_id = transaction_id.strip()

        if transaction_id == "":
            invalid_id_records += 1
            logging.warning("Skipping transaction with empty ID")
            continue

        transaction_id = transaction_id.casefold()

        company = transaction.get("company")

        if not isinstance(company, str):
            invalid_company_records += 1
            logging.warning(
                "Skipping transaction with invalid company: %s",
                transaction_id
            )
            continue

        company = company.strip()

        if company == "":
            invalid_company_records += 1
            logging.warning(
                "Skipping transaction with empty company: %s",
                transaction_id
            )
            continue

        raw_amount = transaction.get("amount")

        if isinstance(raw_amount, str):
            raw_amount = raw_amount.strip()

        if isinstance(raw_amount, bool):
            invalid_amount_records += 1
            logging.warning(
                "Skipping transaction with boolean amount: %s",
                transaction_id
            )
            continue

        try:
            amount = Decimal(str(raw_amount))
        except (ValueError, TypeError, InvalidOperation):
            invalid_amount_records += 1
            logging.warning(
                "Skipping transaction with invalid amount: %s",
                transaction_id
            )
            continue

        if not amount.is_finite():
            invalid_amount_records += 1
            logging.warning(
                "Skipping transaction with non-finite amount: %s",
                transaction_id
            )
            continue

        if amount < 0:
            invalid_amount_records += 1
            logging.warning(
                "Skipping transaction with negative amount: %s",
                transaction_id
            )
            continue

        valid_records += 1

        if transaction_id not in valid_transactions_by_id:
            valid_transactions_by_id[transaction_id] = {
                "company": company,
                "display_company": company,
                "amount": amount,
                "record_count": 1
            }

        else:
            existing = valid_transactions_by_id[transaction_id]
            existing["record_count"] += 1

            existing_company = existing["company"]
            existing_amount = existing["amount"]

            if (
                existing_company.casefold() == company.casefold()
                and existing_amount == amount
            ):
                exact_duplicates += 1
            else:
                conflicted_ids.add(transaction_id)

    for transaction_id in conflicted_ids:
        conflicted_records += (
            valid_transactions_by_id[transaction_id]["record_count"]
        )

    final_exact_duplicate_records = sum(
        record["record_count"] - 1
        for transaction_id, record in valid_transactions_by_id.items()
        if transaction_id not in conflicted_ids
    )

    summary = {}
    valid_transactions = 0

    for transaction_id, record in valid_transactions_by_id.items():

        if transaction_id in conflicted_ids:
            continue

        company = record["company"].casefold()
        display_company = record["display_company"]
        amount = record["amount"]

        if company in summary:
            summary[company]["total"] += amount
            summary[company]["count"] += 1

        else:
            summary[company] = {
                "total": amount,
                "count": 1,
                "display_company": display_company
            }

        valid_transactions += 1

    return (
        summary,
        exact_duplicates,
        valid_records,
        conflicted_ids,
        conflicted_records,
        invalid_id_records,
        invalid_company_records,
        invalid_amount_records,
        records_received,
        valid_transactions,
        invalid_record_types,
        final_exact_duplicate_records
    )



def main(csv_path=None, report_path=None):

    if csv_path is None:
        csv_path = Path(__file__).parent / "transactions.csv"
    else:
        csv_path = Path(csv_path)

    try:
        file = open(
            csv_path,
            "r",
            newline="",
            encoding="utf-8"
        )
    except OSError as error:
        logging.error(
            "Unable to open CSV file %s: %s",
            csv_path,
            error
        )
        raise SystemExit(1)

    try:
        with file:
            reader = csv.DictReader(file, strict=True)
            columns = reader.fieldnames or []

            if not columns:
                logging.error("CSV file is empty or has no header")
                raise SystemExit(1)

            if len(columns) != len(set(columns)):
                logging.error("CSV contains duplicate column names")
                raise SystemExit(1)

            required_columns = {
                "transaction_id",
                "company",
                "amount"
            }

            actual_columns = set(columns)
            missing_columns = required_columns - actual_columns

            if missing_columns:
                logging.error(
                    "CSV is missing required columns: %s",
                    sorted(missing_columns)
                )
                raise SystemExit(1)

            records_received = 0
            transactions = []
            structural_error_records = 0

            for row in reader:
                records_received += 1

                if None in row.values():
                    structural_error_records += 1
                    logging.warning(
                        "Skipping row with missing fields: %s",
                        row
                    )
                    continue

                if None in row:
                    structural_error_records += 1
                    logging.warning(
                        "Skipping row with extra fields: %s",
                        row[None]
                    )
                    continue

                transactions.append(row)

    except csv.Error as error:
        logging.error(
            "Failed to parse CSV file %s: %s",
            csv_path,
            error
        )
        raise SystemExit(1)

    logging.info(
        "CSV loaded successfully: %d records",
        len(transactions)
    )

    if not transactions:
        logging.warning(
            "CSV contains a header but no transaction records"
        )

    (
        summary,
        exact_duplicates,
        valid_records,
        conflicted_ids,
        conflicted_records,
        invalid_id_records,
        invalid_company_records,
        invalid_amount_records,
        records_received,
        valid_transactions,
        invalid_record_types,
        final_exact_duplicate_records
    ) = aggregate_transactions(transactions, records_received)

    validation_rejected_records = (
        structural_error_records
        + invalid_id_records
        + invalid_company_records
        + invalid_amount_records
        + invalid_record_types
    )

    post_validation_excluded_records = (
        final_exact_duplicate_records
        + conflicted_records
    )

    accounted_records = (
        validation_rejected_records
        + post_validation_excluded_records
        + valid_transactions
    )

    if accounted_records == records_received:
        logging.info("Record reconciliation passed")
    else:
        logging.error(
            "Record reconciliation failed: received=%d, accounted=%d",
            records_received,
            accounted_records
        )
        raise SystemExit(1)

    for company, data in summary.items():
        data["average"] = data["total"] / data["count"]

    print("\nCompany Report")
    print("-" * 55)
    print(f'{"Company":<15} {"Total":>12} {"Count":>8} {"Average":>12}')
    print("-" * 55)

    for company, data in summary.items():
        print(
            f"{data['display_company']:<15} "
            f"{data['total']:>12.2f} "
            f"{data['count']:>8} "
            f"{data['average']:>12.2f}"
        )

    print("Exact duplicates : ", exact_duplicates)
    print("Conflicted records :", conflicted_records)

    if conflicted_ids:
        logging.warning(
            "Conflicted transaction IDs: %s",
            sorted(conflicted_ids)
        )
    else:
        logging.info("No Conflicted transaction IDs found")

    print("Invalid ID records : ", invalid_id_records)
    print("Invalid company records : ", invalid_company_records)
    print("Invalid amount records : ", invalid_amount_records)

    valid_record_rate = (
        (valid_records / records_received) * 100
        if records_received > 0
        else 0
    )

    print(f"Valid record rate : {valid_record_rate:.2f}%")

    not_included_records = records_received - valid_transactions

    if not_included_records > 0:
        logging.info(
            "%d records were not included in the final company report",
            not_included_records
        )
    else:
        logging.info(
            "All records were included in the final company report"
        )

    print("Records received : ", records_received)
    print("Structural error records:", structural_error_records)
    print(f"Validation rejected records : {validation_rejected_records}")
    print("Valid Records :", valid_records)
    print("Valid Transactions : ", valid_transactions)
    print(f"Post-validation excluded records : {post_validation_excluded_records}")
    print("Invalid record types : ", invalid_record_types)
    print(f"Accounted records : {accounted_records}")

    if report_path is None:
        report_path = Path(__file__).parent / "company_report.csv"
    else:
        report_path = Path(report_path)

    try:
        with open(
            report_path,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            fieldnames = ["company", "total", "count", "average"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            writer.writeheader()

            for company, data in summary.items():
                writer.writerow({
                    "company": data["display_company"],
                    "total": f"{data['total']:.2f}",
                    "count": data["count"],
                    "average": f"{data['average']:.2f}"
                })

    except OSError as error:
        logging.error("Failed to write company report: %s", error)
        raise SystemExit(1)

    logging.info("Company report saved to: %s", report_path)



if __name__ == "__main__":
    main()
