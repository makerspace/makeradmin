#!/bin/bash
file_path="$1"

if [ -z "$file_path" ]; then
    echo "Usage: db_restore.sh <path to sql file>"
    exit 1
fi

if [ ! -f "$file_path" ]; then
    echo "File not found: $file_path"
    exit 1
fi

# Prompt for confirmation before restoring
while true; do
    read -p "This will delete your current database!! Are you sure you want to continue? " yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

echo ""
echo "Restoring DB..."

cat $file_path | docker compose exec -T db2 bash -c "exec mysql --default-character-set=utf8mb4 -uroot -p\${MYSQL_ROOT_PASSWORD} makeradmin"

echo "Done"
