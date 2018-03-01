Databasstruktur
===============
MultiAccess använder sig av en lokal MSSQL-databas. Denna databas synkas sedan över till en själva centralenheten i passersystemet. Det är oklart om denna synk går att trigga automatiskt, eller om man manuellt behöva trycka på rätt knapp i MultiAccess.


Tabeller
--------
Det finns ett antal tabeller som är intressanta

| Tabell             | Beskrivning                                 |
|--------------------|---------------------------------------------|
| Users              | Innehåller alla nycklar i systemet          |
| Authority          | Behörigheter                                |
| AuthorityInUser    | Koppling mellan nyckel och behörighet       |
| Event              | Händelser / logg                            |
| Resource           | Innehåller alla dörrar etc                  |
| ResourceParam      | Okänt                                       |
| UserNo             | Okänt, men innehåller en väldans massa data |


Skapa testdatabas
-----------------
Det här är en förenklad version av databasen som endast innehåller de tabeller och kolumner vi är intresserade av för tillfället.

`
USE MultiAccess

CREATE TABLE Users (Id int identity PRIMARY KEY NOT NULL, Name varchar(50) NOT NULL, Card varchar(12), Start datetime, Stop datetime, Blocked bit, customerId int, createdTime datetime)

CREATE TABLE AuthorityInUser (Id int identity PRIMARY KEY NOT NULL, UserId int NOT NULL, AuthorityId int NOT NULL, flags int NOT NULL)

INSERT INTO Users (Name, Card, Stop, createdTime, customerId) VALUES('1099', '123456789', '2018-09-14 23:59:59.000', getdate(), 16)

INSERT INTO AuthorityInUser (UserId, AuthorityId, flags) VALUES(SCOPE_IDENTITY(), 23, 0)
`


Uppdatera slutdatum
-------------------
Som ett första steg vill vi endast uppdatera slutdatum på befintliga medlemmar. Detta skall göras med en SQL-query liknande denna:

`UPDATE Users SET Stop='2018-12-24 23:59:59.000' WHERE Name='1099' AND customerId=16`

***customerId*** är 16 för Stockholm Makerspace

***Name*** är det medlemsnummer som medlemmen har i Makeradmin.


Lägg till användare
-------------------
Denna behöver kontrolleras noga innan vi ger oss in på detta. Se `Skapa testdatabas`. 

**TODO**: Kolla upp om tabellen `UserNo` har någon påverkan.

***AuthorityId*** är 23 för vanliga medlemmar på Stockholm Makerspace


Konvertera RFID-nummer
----------------------
Aptus använder ett lite annorlunda format för att lagra RFID-numret. Den innehåller bland annat husnumret och trunkerar till 12 siffror. Det är viktigt att man har rätt typ av läsare som inkluderar husnumret och att man gör konverteringen korrekt. Mer om detta senare.