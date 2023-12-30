import csv
import sys
from collections import defaultdict
from datetime import datetime

year = sys.argv[1]
inputs = f"transactions_{year}.tsv"
output = f"monthly_transactions_summary_{year}.tsv"

monthly_totals = defaultdict(float)
debit_totals = defaultdict(lambda: defaultdict(float))
credit_totals = defaultdict(lambda: defaultdict(float))

with open(inputs, "r") as file:
    reader = csv.DictReader(file, delimiter="\t")
    for row in reader:
        date = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
        year_month = date.strftime("%Y-%m")
        amount = float(row["amount"])
        monthly_totals[year_month] += amount
        account = row["account"]
        debits_fraction = float(row["debits"])
        credits_fraction = float(row["credits"])
        cost_center = row["cost_center"]
        debit_totals[year_month][(account, cost_center)] += amount * debits_fraction
        credit_totals[year_month][(account, cost_center)] += amount * credits_fraction

with open(output, "w", newline="") as file:
    writer = csv.writer(file, delimiter="\t")
    headers = ["Period", "AmountDebit", "AmountCredit", "Account", "CostCenter"]
    writer.writerow(headers)

    for year_month in sorted(monthly_totals.keys()):
        for acc_cost_tuple in debit_totals[year_month].keys():
            writer.writerow(
                [
                    year_month,
                    debit_totals[year_month][acc_cost_tuple],
                    credit_totals[year_month][acc_cost_tuple],
                    acc_cost_tuple[0],
                    acc_cost_tuple[1],
                ]
            )
print(f"Data Compiled to {output}")
