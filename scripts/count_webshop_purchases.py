import subprocess
from argparse import ArgumentParser
from datetime import date

items = [
    "Corrugated Cardboard 1180x780mm, 2,5mm",
    "Ball nose end mill for aluminum- 2.0mm, 2-skär",
    "Ball nose end mill for aluminum- 2.5mm, 2-skär",
    "Ball nose end mill for aluminum- 3.0mm, 2-skär",
    "Ball nose end mill for aluminum- 4.0mm, 2-skär",
    "Ball nose end mill for aluminum- 6mm, 2-skär",
    "Ball nose end mill for aluminum- 8mm, 2-skär",
    "Ball nose end mill, 3.175mm for wood & plastic",
    "Ball nose end mill, 4mm for wood & plastic",
    "Ball nose end mill, 6mm for wood & plastic",
    "End mill for aluminum 2mm, 3-skär",
    "End mill for aluminum 3mm, 3-skär",
    "End mill for aluminum 4mm, 3-skär",
    "End mill for aluminum- 2.5mm, 2-skär",
    "End mill for aluminum- 2mm, 3-skär",
    "End mill for aluminum- 6mm, 3-skär",
    "End mill for aluminum- 8mm, 3-skär",
    "End mill for plastic- 2 x 12mm, 1-skär",
    "End mill for plastic- 4 x 22mm, 1-skär",
    "End mill for plastic- 6 x 28mm, 1-skär",
    "End mill for steel- 12mm, 3-skär",
    "End mill for steel- 4mm, 3-skär",
    "End mill for steel- 6mm, 3-skär",
    "End mill for steel- 8mm, 3-skär",
    "End mill, 3.175mm for wood & plastics",
    "End mill, 4mm for wood & plastics",
    "End mill, 6mm for wood & plastics",
    "V-Groove 60° cutter for wood/plastics",
    "Chamfer cutter- 90 deg drill bit",
    "Half-round engraving bit- 30 deg 0.1mm",
    "Cutting insert- DCGT-0702-STEEL",
    "Cutting insert- DCMT-0702-ALU",
    "Cutting insert- ER-16-AG60-ALU",
    "Cutting insert- ER-16-AG60-STEEL",
    "Cutting insert- IR-16-AG60-ALU",
    "Cutting insert- IR-16-AG60-STEEL",
    "Cutting insert- MGGN-200-ALU",
    "Cutting insert- MGMN-200-STEEL",
    "Cutting insert- RCGT-0803-ALU",
    "Cutting insert- RCMT-0803-STEEL",
    "Cutting insert- WNMG-0604-ALU",
    "Cutting insert- WNMG-0604-STEEL",
    "Lathe blank- HSS 10x10x100mm",
    "Stämpelgummi A5",
    "Gravyrlaminat vit/svart",
    "Gravyrlaminat gul/svart",
]

arg_parser = ArgumentParser()
arg_parser.add_argument("--start-date", type=date.fromisoformat, required=True, help="Format: YYYY-MM-DD")
arg_parser.add_argument("--end-date", type=date.fromisoformat, required=True, help="Format: YYYY-MM-DD")
args = arg_parser.parse_args()

start_date = args.start_date.strftime("%Y-%m-%d")
end_date = args.end_date.strftime("%Y-%m-%d")

sqls = []
for item in items:
    sql = f"""select '{item}', sum(count) from webshop_transaction_contents \
        JOIN webshop_transactions ON webshop_transactions.id=transaction_id \
        where webshop_transactions.created_at>'{start_date}' AND webshop_transactions.created_at<'{end_date}' AND product_id=(select id from webshop_products where name='{item}');"""
    sqls.append(sql)

try:
    proc = subprocess.run(
        [
            "docker",
	    "compose",
            "exec",
            "-T",
            "db2",
            "bash",
            "-c",
            "mysql --batch --disable-column-names --default-character-set=utf8mb4 -uroot -p${MYSQL_ROOT_PASSWORD} makeradmin",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        input=";".join(sqls).encode("utf-8"),
    )
except subprocess.CalledProcessError as e:
    print(e.stderr.decode("utf-8"))
    RED = "\033[1;31m"
    RESET = "\033[0;0m"
    print(f"{RED}Failed to run the SQL query. Make sure makeradmin is currently running on this machine.{RESET}")
    exit(1)

res = proc.stdout.decode("utf-8").strip()
# res = res.replace("mysql: [Warning] Using a password on the command line interface can be insecure.", "")
print(res)
