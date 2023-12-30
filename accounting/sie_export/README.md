# Export of SIE-files

Example run:

```console
python3 make_booking.py --financial-year 2021 --signer "Aron Granberg" --makeradmin-tsv ./transactions_2021.tsv --stripe-csv ./Itemized_balance_change_from_activity_charge_SEK_2021-01-01_to_2021-12-31_Europe-Stockholm.csv --output export_2021.si
```

Filen formatteras enligt [standarden](https://sie.se/wp-content/uploads/2020/05/SIE_filformat_ver_4B_ENGLISH.pdf) med CP437-kodning.

## Exportera från makeradmin

Exportera data från makeradmin genom att SSH:a dit. Kör sedan `./export_transactions.sh` med räkneskapsåret som argument.

```bash
./export_transactions.sh 2021
```

Du kan potentiellt behöva ge permission till dig själv att skriva i foldern (eller med `sudo su johank`).

Du kan överföra filen till din dator med t.ex. SCP:

```bash
scp aron@makeradmin.se:/home/johank/docker/MakerAdmin/makeradmin/transactions_2021.tsv .
```

## Exportera från Stripe

Exportera data från Stripe genom att logga in och gå sedan till _Reports_ -> _Balance_ -> Ändra till "Last Year" -> _Balance change from activity_ -> _Charges_ -> _Download_.
