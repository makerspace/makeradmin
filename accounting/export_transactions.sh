#!/bin/bash
year=$1
target="transactions_$1.tsv"
echo "Exporting year $year to $target"
set -e
docker compose exec db2 bash -c "mysql -uroot --batch --default-character-set=utf8 --raw -p\${MYSQL_ROOT_PASSWORD} makeradmin -e \"select webshop_transactions.created_at, webshop_transactions.id, webshop_transaction_contents.amount, webshop_products.name, webshop_transaction_accounts.account, webshop_transaction_cost_centers.cost_center, webshop_product_accounting.debits, webshop_product_accounting.credits from webshop_transactions LEFT JOIN membership_members ON webshop_transactions.member_id=membership_members.member_id LEFT JOIN webshop_transaction_contents ON webshop_transactions.id=webshop_transaction_contents.transaction_id LEFT JOIN webshop_products ON webshop_products.id=webshop_transaction_contents.product_id LEFT JOIN webshop_product_accounting ON webshop_product_accounting.product_id=webshop_products.id LEFT JOIN webshop_transaction_accounts ON webshop_transaction_accounts.id=webshop_product_accounting.account_id LEFT JOIN webshop_transaction_cost_centers ON webshop_transaction_cost_centers.id=webshop_product_accounting.cost_center_id WHERE webshop_transactions.status='completed' AND webshop_transactions.created_at>='$year-01-01' AND webshop_transactions.created_at<='$year-12-31 23:59:59' ORDER BY webshop_transactions.created_at;\"" | grep -v "mysql: \[Warning\] Using a password" > $target
