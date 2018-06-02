[![Build Status](https://travis-ci.org/makerspace/MakerAdmin-MultiAccessProgram.svg?branch=travis-ci-integration)](https://travis-ci.org/makerspace/MakerAdmin-MultiAccessProgram)

**TODO** Update this document.

Synkroniseringsmodul mellan Makeradmin och MultiAccess
======================================================

En Windowsapplikation som automatiskt hämtar hem data från Makeradmin och uppdaterar slutdatum på nycklar i MultiAccess


MultiAccess
-----------
Multiaccess är en programvara utvecklad av Aptus och används för att administrera deras passersystem. Programvaran är ganska föråldrad och verkar inte längre underhållas. Det är dock ett system som fortfarande verkar vara relativt vanlig på äldre fastigheter.


Tidigare versioner av denna modul
---------------------------------
Det finns även en tidigare version av denna synkroniseringsmodul. Den tidigare versionen gör ingen automatisk synkronisering, utan är endast ett verktyg för att göra en avstämning och kolla att de två olika databaserna stämmer överens. Alla ändringar måste göras manuellt.

https://github.com/MakersOfSweden/MakerAdmin-MultiAccessSync


Kravspec version 1
------------------

Version 1 implementerar de mest kritiska funktionerna som kommer spara väldigt mycket tid.

 * Ladda hem JSON data via ett REST API
 * Uppdatera raderna en och en med en "LIMIT 1" och vara överdrivet noga med att det verkligen är rätt rad som uppdateras
 * Föra en logg över exakt vilka åtgärder som görs
 * Om det är möjligt även föra en logg över vilka exakta SQL-kommandon som körs
 * Alltid spara en backup av en rad innan den ändras
 * Spara ner datumet för när senaste synkroniseringen gjordes
 * Skicka upp och lagra nödvändig data på servern (Loggar? Backuper?)
 * Autostarta programmet
 * Konfiguerationsfil (Se `Installation`)


Kravspec version 2
------------------

Version 2 är önskvärd i framtiden, men inget vi lägger energi på förän version 1 är i full drift.

 * Visa ett UI för användaren med en logg, datum för senaste uppdatering, felmeddelanden, konfiguration, etc
 * Möjlighet att skapa helt nya nycklar
 * Möjlighet att ta bort befintliga nycklar


Pseudo-kod
----------
**TODO**: Skriv pseudo-kod för hur programmet skall fungera


Databasstruktur
---------------
Se [Docs/Database.md](Docs/Database.md)


Development Environment
------------------------

Written in Python (requires Python >= 3.6).

### Install dependencies
`make init`

This installs the Python dependencies described in `requirements.txt`

### Run tests
`make test`

### Create windows executables
`make dist`

Installation
------------
**TODO**: Lägg in instruktioner för hur man installerar och konfiguerar programmet i den riktiga miljön
Följande parametrar behöver ändras i konfigurationsfilern: DbHost, DbUser, DbPassword, DbName, ApiUrl, ApiBearer, ApiPollInterval, KeyCustomerId, KeyAuthorityId
