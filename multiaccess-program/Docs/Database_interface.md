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
7> select * from AuthorityInUser;
8> go
```

```bash
# Output to text file
$ sqlcmd -S '(local)\SQLEXPRESS' -d MultiAccess -Q "select * from Users" -o "output.txt"
```

### The tables!
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
|     *txt*      |     *txt*      |    NULL    |   NULL   |    NULL     |    0     |    NULL     |    NULL    |

### [pymssql](http://pymssql.org/en/stable/)
Installing with pip: `pip install pymssql`

### pyodbc
Installing with pip: `pip install pyodbc`
[Look under *Connecting Python to Microsoft SQL Server*](https://www.easysoft.com/developer/languages/python/pyodbc.html) for instructions on how to connect to MSSQL through Python.

It should basically be

```python
>>> import pyodbc
>>> cnxn = pyodbc.connect("DSN=MSSQL-PYTHON")
>>> cursor = cnxn.cursor()
>>> cursor.tables()
>>> rows = cursor.fetchall()
>>> for row in rows:
...     print(row.table_name)
...
Categories
CustomerCustomerDemo
CustomerDemographics
Customers
Employees
EmployeeTerritories
.
.
.
>>> exit()
```

> In the pyodbc.connect() call, replace MSSQL-PYTHON with the name of your SQL Server ODBC driver data source.


It seems that we still need to install a separate driver for connecting to the API without the `sqlcmd` program.
> Installing the Microsoft ODBC Driver for SQL Server provides native connectivity from Windows to Microsoft SQL Server

**Quote**: https://www.microsoft.com/en-us/download/details.aspx?id=36434

```python
>>> con = pyodbc.connect(Trusted_Connection='yes', driver = '{SQL Server}', serv
er = '(local)\SQLEXPRESS', database = 'MultiAccess')
>>> cur.execute("select * from Users")
>>> cur.fetchall()
{"Results ... "}
```
