# Interfacing with the MultiAccess database
We want to be able to alter the MultiAccess database without actually using the program. Therefore, we are aiming to write a program that can automatically get data from the MakerAdmin server (via a service) and then write it to the MultiAccess database. We need the program to be an executable without dependencies so that we can run it without having to install anything.

## [Running a Python program without dependencies][StackOverflow Python Executable generation]

Python could be an alternative if we can run it without installing it. There are two strong proposals, after a quick glance, for packing the scripts into an executable:

[StackOverflow Python Executable generation]: https://stackoverflow.com/questions/5458048/how-to-make-a-python-script-standalone-executable-to-run-without-any-dependency
* http://www.py2exe.org/: 
* http://www.pyinstaller.org/: Searches dependencies and can put them all into a *one folder* or *one file* executable.

## Interfacing with the MSSQL database natively
The database can be interfaced with the MSSQL command line utility `sqlcmd` that comes with the MultiAccess installation.

##### Opening the database:
```bash
# Open the database
$ sqlcmd -S '(local)\SQLEXPRESS' -d MultiAccess
```

##### Reading some tables from the database
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

##### One-liner with query and output to text file
```bash
# Output to text file
$ sqlcmd -S '(local)\SQLEXPRESS' -d MultiAccess -Q "select * from Users" -o "output.txt"
```

### The tables!
Let's look some at the tables that exist in the database...

Formattings:

* *datetime*: `2018-03-15 00:00:00.000`
* *NULL/Num*: Either `NULL` or an integer
* *Inc*: Incrementing, unique (?) number

#### 'Users'
Contains the following 'important' columns with the corresponding formats

|  Name  |  Code  |   Start    |    Stop    |  Blocked   | Changed | customerId | createdTime |  Id   |
|:------:|:------:|:----------:|:----------:|:----------:|:-------:|:----------:|:-----------:|:-----:|
| *text* | *text* | *datetime* | *datetime* | *NULL/Num* |  *num*  | *NULL/Num* | *datetime*  | *Inc* |

Other unused (?) columns: 

| `f0` ... `f14` | `fi0` .. `fi3` | PortalName | Password | PortalLevel | pulBlock | PTFirstName | PTLastName |
|:--------------:|:--------------:|:----------:|:--------:|:-----------:|:--------:|:-----------:|:----------:|
|     *txt*      |     *txt*      |    NULL    |   NULL   |    NULL     |    0     |    NULL     |    NULL    |

## Interfacing with the MSSQL database through Python
### [pymssql](http://pymssql.org/en/stable/)
Not tested yet...
Installing with pip: `pip install pymssql`

### [pyodbc](https://mkleehammer.github.io/pyodbc/)
Works!
Installing with pip: `pip install pyodbc`

#### Example reading from MultiAccess with pyodbc
```python
>>> import pyodbc
>>> connection = pyodbc.connect(Trusted_Connection='yes', driver = '{SQL Server}', \
        server = '(local)\SQLEXPRESS', database = 'MultiAccess')
>>> cursor = connection.cursor()
>>> cursor.execute("select * from Users")
<pyodbc.Cursor object at 0x00000252B06584E0>
>>> cursor.fetchall()
[('Name Namesson', '1234', '917000000', None, None, False, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, 0, None, None, 1, None, None, None, False, None, None),
 ('Anders Andersson', None, '123456789', datetime.datetime(2018, 3, 14, 0, 0), datetime.datetime(2018, 3, 15, 0, 0), None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, 0, 1, datetime.datetime(2018, 3, 14, 20, 14, 12), 2, None, None, None, False, None, None)]

>>> cursor.tables()
>>> rows = cursor.fetchall()
>>> for row in rows:
...     print(row.table_name)
...
Address
[...]
Authority
AuthorityInUser
[...]
Customer
[...]
Event
[...]
Users
[...]
>>> len(rows)
505
```

As you can see, there are 505 (!) tables in the database.