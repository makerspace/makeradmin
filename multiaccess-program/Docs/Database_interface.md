# Key exchange development

## [Running a Python program without dependencies][StackOverflow Python Executable generation]

[StackOverflow Python Executable generation]: https://stackoverflow.com/questions/5458048/how-to-make-a-python-script-standalone-executable-to-run-without-any-dependency
* http://www.py2exe.org/: 
* http://www.pyinstaller.org/: Searches dependencies and can put them all into a *one folder* or *one file* executable.

## Interfacing with the MSSQL database directly
```bash
# Open the database
$ sqlcmd -S '(local)\SQLEXPRESS' -d MultiAccess
```
```bash
# Show the tables
1> select * from sysobjects where xtype = 'U'
2> go
# Besökare
3> select * from Users;
4> go
# Kund
5> select * from Customer;
6> go
# Behörighet
7> select * from Authority;
8> go
```

```bash
# Output to text file
$ sqlcmd -S '(local)\SQLEXPRESS' -d MultiAccess -Q "select * from Users" -o "output.txt"
```

### `Users` table
Contains the following columns with the corresponding formats

|  Name  |  Code  |   Start    |    Stop    |  Blocked   | Changed | customerId | createdTime |  Id   |
|:------:|:------:|:----------:|:----------:|:----------:|:-------:|:----------:|:-----------:|:-----:|
| *text* | *text* | *datetime* | *datetime* | *NULL/Num* |  *num*  | *NULL/Num* | *datetime*  | *Inc* |


Formattings:

* *datetime*: `2018-03-15 00:00:00.000`
* *NULL/Num*: Either `NULL` or a number

Other columns: 

| `f0` ... `f14` | `fi0` .. `fi3` | PortalName | Password | PortalLevel | pulBlock | PTFirstName | PTLastName |
|:--------------:|:--------------:|:----------:|:--------:|:-----------:|:--------:|:-----------:|:----------:|
|                |                |    NULL    |   NULL   |    NULL     |    0     |    NULL     |    NULL    |