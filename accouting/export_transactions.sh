#!/bin/bash
year=$1
target="transactions_$1.tsv"
echo "Exporting year $year to $target"
set -e
docker compose exec db2 bash -c "mysql -uroot --batch --default-character-set=utf8 --raw -p\${MYSQL_ROOT_PASSWORD} makeradmin -e \"select webshop_transactions.created_at, webshop_transactions.id, webshop_transaction_contents.amount, webshop_products.name from webshop_transactions LEFT JOIN membership_members ON webshop_transactions.member_id=membership_members.member_id LEFT JOIN webshop_transaction_contents ON webshop_transactions.id=webshop_transaction_contents.transaction_id LEFT JOIN webshop_products ON webshop_products.id=webshop_transaction_contents.product_id WHERE webshop_transactions.status='completed' AND webshop_transactions.created_at>='$year-01-01' AND webshop_transactions.created_at<='$year-12-31 23:59:59' ORDER BY webshop_transactions.created_at;\"" | grep -v "mysql: \[Warning\] Using a password" > $target 
