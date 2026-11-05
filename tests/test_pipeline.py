import tempfile
import csv
from pathlib import Path
from unittest.mock import patch
import unittest
from read_csv import main, aggregate_transactions
from decimal import Decimal
from contextlib import redirect_stdout
from io import StringIO


class TestTransactionPipeline(unittest.TestCase):

    # 1. Valid transaction
    def test_valid_transaction(self):
        transactions = [
            {
                "transaction_id": "T001",
                "company": "Amazon",
                "amount": "100"
            }
        ]

        result = aggregate_transactions(transactions, 1)

        self.assertEqual(result[0]["amazon"]["total"], 100)
        self.assertEqual(result[0]["amazon"]["count"], 1)

    # 2. Negative amount
    def test_negative_amount(self):
        transactions = [
            {
                "transaction_id": "T002",
                "company": "Amazon",
                "amount": "-500"
            }
        ]

        result = aggregate_transactions(transactions, 1)

        self.assertEqual(result[0], {})
        self.assertEqual(result[7], 1)
        self.assertEqual(result[9], 0)

    # 3. Invalid amount
    def test_invalid_amount(self):
        transactions = [
            {
                "transaction_id": "T003",
                "company": "Amazon",
                "amount": "abc"
            }
        ]

        result = aggregate_transactions(transactions, 1)

        self.assertEqual(result[0], {})
        self.assertEqual(result[7], 1)
        self.assertEqual(result[9], 0)

    # 4. Exact duplicate
    def test_exact_duplicate(self):
        transactions = [
            {
                "transaction_id": "T004",
                "company": "Amazon",
                "amount": "500"
            },
            {
                "transaction_id": "T004",
                "company": "Amazon",
                "amount": "500"
            }
        ]

        result = aggregate_transactions(transactions, 2)

        self.assertEqual(result[0]["amazon"]["total"], 500)
        self.assertEqual(result[0]["amazon"]["count"], 1)
        self.assertEqual(result[1], 1)
        self.assertEqual(result[9], 1)

    # 5. Conflicting transactions
    def test_conflicting_transactions(self):
        transactions = [
            {
                "transaction_id": "T005",
                "company": "Amazon",
                "amount": "500"
            },
            {
                "transaction_id": "T005",
                "company": "Amazon",
                "amount": "700"
            }
        ]

        result = aggregate_transactions(transactions, 2)

        self.assertEqual(result[0], {})
        self.assertEqual(result[3], {"t005"})
        self.assertEqual(result[4], 2)
        self.assertEqual(result[9], 0)

    # 6. Case-insensitive transaction ID
    def test_case_insensitive_transaction_id(self):
        transactions = [
            {
                "transaction_id": "T006",
                "company": "Amazon",
                "amount": "300"
            },
            {
                "transaction_id": "t006",
                "company": "Amazon",
                "amount": "300"
            }
        ]

        result = aggregate_transactions(transactions, 2)

        self.assertEqual(result[0]["amazon"]["total"], 300)
        self.assertEqual(result[1], 1)
        self.assertEqual(result[2], 2)
        self.assertEqual(result[9], 1)

    # 7. Missing transaction ID
    def test_missing_transaction_id(self):
        transactions = [
            {
                "company": "Amazon",
                "amount": "500"
            }
        ]

        result = aggregate_transactions(transactions, 1)

        self.assertEqual(result[0], {})
        self.assertEqual(result[5], 1)

    # 8. Missing company
    def test_missing_company(self):
        transactions = [
            {
                "transaction_id": "T011",
                "amount": "500"
            }
        ]

        result = aggregate_transactions(transactions, 1)

        self.assertEqual(result[0], {})
        self.assertEqual(result[6], 1)

    # 9. Whitespace-only transaction ID
    def test_whitespace_transaction_id(self):
        transactions = [
            {
                "transaction_id": "   ",
                "company": "Amazon",
                "amount": "500"
            }
        ]

        result = aggregate_transactions(transactions, 1)

        self.assertEqual(result[0], {})
        self.assertEqual(result[5], 1)

    # 10. Whitespace-only company name
    def test_whitespace_company(self):
        transactions = [
            {
                "transaction_id": "T012",
                "company": "   ",
                "amount": "500"
            }
        ]

        result = aggregate_transactions(transactions, 1)

        self.assertEqual(result[0], {})
        self.assertEqual(result[6], 1)

    # 11. Zero amount
    def test_zero_amount(self):
        transactions = [
            {
                "transaction_id": "T013",
                "company": "Amazon",
                "amount": "0"
            }
        ]

        result = aggregate_transactions(transactions, 1)

        self.assertEqual(result[0]["amazon"]["total"], 0)
        self.assertEqual(result[0]["amazon"]["count"], 1)
        self.assertEqual(result[9], 1)

    # 12. NaN amount
    def test_nan_amount(self):
        transactions = [
            {
                "transaction_id": "T014",
                "company": "Amazon",
                "amount": "NaN"
            }
        ]

        result = aggregate_transactions(transactions, 1)

        self.assertEqual(result[0], {})
        self.assertEqual(result[7], 1)

    # 13. Infinity amount
    def test_infinity_amount(self):
        transactions = [
            {
                "transaction_id": "T015",
                "company": "Amazon",
                "amount": "Infinity"
            }
        ]

        result = aggregate_transactions(transactions, 1)

        self.assertEqual(result[0], {})
        self.assertEqual(result[7], 1)

    # 14. Invalid record type
    def test_invalid_record_type(self):
        transactions = [None]

        result = aggregate_transactions(transactions, 1)

        self.assertEqual(result[0], {})
        self.assertEqual(result[10], 1)
        self.assertEqual(result[9], 0)

    # 15. Exact duplicate followed by a conflict
    def test_duplicate_followed_by_conflict(self):
        transactions = [
            {
                "transaction_id": "T016",
                "company": "Amazon",
                "amount": "500"
            },
            {
                "transaction_id": "T016",
                "company": "Amazon",
                "amount": "500"
            },
            {
                "transaction_id": "T016",
                "company": "Amazon",
                "amount": "700"
            }
        ]

        result = aggregate_transactions(transactions, 3)

        self.assertEqual(result[0], {})
        self.assertEqual(result[3], {"t016"})
        self.assertEqual(result[4], 3)
        self.assertEqual(result[9], 0)

    def test_main_generates_company_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:

            csv_path = Path(temp_dir) / "test_transactions.csv"
            report_path = Path(temp_dir) / "test_report.csv"

            with open(csv_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=["transaction_id", "company", "amount"]
                )

                writer.writeheader()

                writer.writerow({
                    "transaction_id": "T101",
                    "company": "Amazon",
                    "amount": "500"
                })

                writer.writerow({
                    "transaction_id": "T102",
                    "company": "Amazon",
                    "amount": "300"
                })

            with patch("builtins.print"):
                main(csv_path, report_path)

            self.assertTrue(report_path.exists())

            with open(report_path, "r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                rows = list(reader)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["company"], "Amazon")
            self.assertEqual(rows[0]["total"], "800.00")
            self.assertEqual(rows[0]["count"], "2")
            self.assertEqual(rows[0]["average"], "400.00")

    def test_missing_csv_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "does_not_exist.csv"
            report_path = Path(temp_dir) / "test_report.csv"

            with self.assertRaises(SystemExit) as context:
                main(csv_path, report_path)

            self.assertEqual(context.exception.code, 1)
            self.assertFalse(report_path.exists())

    def test_empty_csv_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "empty.csv"
            report_path = Path(temp_dir) / "test_report.csv"

            csv_path.write_text("", encoding="utf-8")

            with self.assertRaises(SystemExit) as context:
                main(csv_path, report_path)

            self.assertEqual(context.exception.code, 1)
            self.assertFalse(report_path.exists())

    def test_missing_required_column(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "missing_column.csv"
            report_path = Path(temp_dir) / "test_report.csv"

            with open(csv_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=["transaction_id", "company"]
                )
                writer.writeheader()

            with self.assertRaises(SystemExit) as context:
                main(csv_path, report_path)

            self.assertEqual(context.exception.code, 1)
            self.assertFalse(report_path.exists())

    def test_duplicate_csv_headers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "duplicate_headers.csv"
            report_path = Path(temp_dir) / "test_report.csv"

            csv_path.write_text(
                "transaction_id,company,amount,amount\n",
                encoding="utf-8"
            )

            with self.assertRaises(SystemExit) as context:
                main(csv_path, report_path)

            self.assertEqual(context.exception.code, 1)
            self.assertFalse(report_path.exists())

    def test_malformed_csv_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "malformed.csv"
            report_path = Path(temp_dir) / "test_report.csv"

            with open(csv_path, "w", newline="", encoding="utf-8") as file:
                file.write(
                    "transaction_id,company,amount\n"
                    "T101,Amazon,500\n"
                    "T102,Amazon\n"
                    "T103,Amazon,300,Extra\n"
                    "T104,Amazon,200\n"
                )

            with patch("builtins.print"):
                main(csv_path, report_path)

            with open(report_path, "r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                rows = list(reader)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["total"], "700.00")
            self.assertEqual(rows[0]["count"], "2")

    def test_csv_with_headers_but_no_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "headers_only.csv"
            report_path = Path(temp_dir) / "test_report.csv"

            csv_path.write_text(
                "transaction_id,company,amount\n",
                encoding="utf-8"
            )

            with patch("builtins.print"):
                main(csv_path, report_path)

            self.assertTrue(report_path.exists())

            with open(report_path, "r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                rows = list(reader)

            self.assertEqual(len(rows), 0)

    def test_case_insensitive_company_aggregation(self):
        records = [
            {
                "transaction_id": "T101",
                "company": "Amazon",
                "amount": "100"
            },
            {
                "transaction_id": "T102",
                "company": "amazon",
                "amount": "200"
            },
            {
                "transaction_id": "T103",
                "company": "AMAZON",
                "amount": "300"
            }
        ]

        result = aggregate_transactions(records, len(records))
        summary = result[0]

        self.assertEqual(len(summary), 1)
        self.assertEqual(summary["amazon"]["total"], Decimal("600"))
        self.assertEqual(summary["amazon"]["count"], 3)

    def test_company_display_name_preserved(self):
        records = [
            {
                "transaction_id": "T101",
                "company": "Amazon",
                "amount": "100"
            },
            {
                "transaction_id": "T102",
                "company": "amazon",
                "amount": "200"
            },
            {
                "transaction_id": "T103",
                "company": "AMAZON",
                "amount": "300"
            }
        ]

        result = aggregate_transactions(records, len(records))
        summary = result[0]

        self.assertEqual(
            summary["amazon"]["display_company"],
            "Amazon"
        )

    def test_report_write_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "transactions.csv"

            report_path = Path(temp_dir) / "missing_folder" / "report.csv"

            csv_path.write_text(
                "transaction_id,company,amount\n"
                "T101,Amazon,500\n",
                encoding="utf-8"
            )

            with patch("builtins.print"):
                with self.assertRaises(SystemExit) as context:
                    main(csv_path, report_path)

            self.assertEqual(context.exception.code, 1)
            self.assertFalse(report_path.exists())

    def test_final_exact_duplicates_excludes_conflicted_ids(self):
        records = [
            {"transaction_id": "T101", "company": "Amazon", "amount": "500"},
            {"transaction_id": "T101", "company": "Amazon", "amount": "500"},
            {"transaction_id": "T101", "company": "Amazon", "amount": "700"},
            {"transaction_id": "T102", "company": "Flipkart", "amount": "300"}
        ]

        result = aggregate_transactions(records, len(records))

        summary = result[0]
        conflicted_records = result[4]
        valid_transactions = result[9]

        self.assertEqual(conflicted_records, 3)
        self.assertEqual(valid_transactions, 1)
        self.assertEqual(summary["flipkart"]["count"], 1)
        self.assertEqual(result[11], 0)

    def test_final_exact_duplicates_for_non_conflicted_id(self):
        records = [
            {"transaction_id": "T101", "company": "Amazon", "amount": "500"},
            {"transaction_id": "T101", "company": "Amazon", "amount": "500"},
            {"transaction_id": "T101", "company": "Amazon", "amount": "500"}
        ]

        result = aggregate_transactions(records, len(records))

        self.assertEqual(result[4], 0)   # Conflicted records
        self.assertEqual(result[9], 1)   # Valid transactions
        self.assertEqual(result[11], 2)  # Final exact duplicates

    def test_mixed_record_reconciliation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "transactions.csv"
            report_path = Path(temp_dir) / "report.csv"

            csv_path.write_text(
                "transaction_id,company,amount\n"
                "X001,Amazon,100,EXTRA\n"
                "I001,Amazon,abc\n"
                "I002,,200\n"
                "D001,Amazon,500\n"
                "D001,Amazon,500\n"
                "D001,Amazon,500\n"
                "C001,Amazon,500\n"
                "C001,Amazon,500\n"
                "C001,Amazon,700\n"
                "A001,Amazon,100\n"
                "A002,Flipkart,200\n"
                "A003,Google,300\n",
                encoding="utf-8"
            )

            output = StringIO()

            with redirect_stdout(output):
                with self.assertLogs(level="INFO") as logs:
                    main(csv_path, report_path)

            result = output.getvalue()

            self.assertIn("Records received :  12", result)
            self.assertIn("Valid Transactions :  4", result)
            self.assertIn("Post-validation excluded records : 5", result)
            self.assertIn("Accounted records : 12", result)

            self.assertTrue(
                any("Record reconciliation passed" in message
                    for message in logs.output)
            )

            with open(report_path, "r", newline="", encoding="utf-8") as file:
                report = list(csv.DictReader(file))

            self.assertEqual(len(report), 3)

            amazon = next(row for row in report if row["company"] == "Amazon")

            self.assertEqual(amazon["total"], "600.00")
            self.assertEqual(amazon["count"], "2")

    def test_reconciliation_failure_stops_pipeline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "transactions.csv"
            report_path = Path(temp_dir) / "report.csv"

            csv_path.write_text(
                "transaction_id,company,amount\n"
                "T101,Amazon,500\n",
                encoding="utf-8"
            )

            # Simulate an incorrect reconciliation result.
            mocked_result = (
                {},       # summary
                0,        # exact_duplicates
                0,        # valid_records
                set(),    # conflicted_ids
                0,        # conflicted_records
                0,        # invalid_id_records
                0,        # invalid_company_records
                0,        # invalid_amount_records
                1,        # records_received
                0,        # valid_transactions
                0,        # invalid_record_types
                0         # final_exact_duplicate_records
            )

            with patch(
                "read_csv.aggregate_transactions",
                return_value=mocked_result
            ):
                with patch("builtins.print"):
                    with self.assertRaises(SystemExit) as context:
                        main(csv_path, report_path)

            self.assertEqual(context.exception.code, 1)
            self.assertFalse(report_path.exists())

    def test_malformed_csv_syntax(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "transactions.csv"
            report_path = Path(temp_dir) / "company_report.csv"

            csv_path.write_text(
                'transaction_id,company,amount\n'
                'T001,"Amazon,4999\n',
                encoding="utf-8"
            )

            with self.assertRaises(SystemExit) as error:
                main(csv_path, report_path)

            self.assertEqual(error.exception.code, 1)
            self.assertFalse(report_path.exists())


if __name__ == "__main__":
    unittest.main()
