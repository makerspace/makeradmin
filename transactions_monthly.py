import sys
import csv
from collections import defaultdict
from datetime import datetime

year = sys.argv[1]
inputs = f"transactions_{year}.tsv"
output = f"monthly_transactions_summary_{year}.tsv"

monthly_totals = defaultdict(float)
monthly_transactions = defaultdict(int)
account_totals = defaultdict(lambda: defaultdict(float))
cost_center_totals = defaultdict(lambda: defaultdict(float))

with open(inputs, 'r') as file:
    reader = csv.DictReader(file, delimiter='\t')
    for row in reader:
        date = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
        year_month = date.strftime('%Y-%m')
        amount = float(row['amount'])
        monthly_totals[year_month] += amount
        monthly_transactions[year_month] += 1
        account = row['account']
        cost_center = row['cost_center']
        account_totals[year_month][account] += amount
        cost_center_totals[year_month][cost_center] += amount

with open(output, 'w', newline='') as file:
    writer = csv.writer(file, delimiter='\t')
    headers = ['Period', 'AmountDebit','AmountCredit', 'Account', 'CostCenter']
    writer.writerow(headers)

    for year_month in sorted(monthly_totals.keys()):
        for account,cost_center in zip(account_totals[year_month],cost_center_totals[year_month]): 
            writer.writerow([
                year_month,  
                account_totals[year_month][account], 
                cost_center_totals[year_month][cost_center],
                account,
                cost_center
            ])
            
print(f"Data sammanställd till {output}")



