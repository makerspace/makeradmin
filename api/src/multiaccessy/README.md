# Påläsning av API-dokumentation
* export av nyligen labbmedlemmar + telefonnummer
* knapp i makeradmin för att skicka ut Accessy-länk manuellt. Används vid medlemsintroduktioner.
* dela upp i veckovis access? Synka upp midnatt De som betalat före dess får access. Annars får man vänta till nästa vecka.
  * Se till att alltid synka upp några veckor i förväg så att folk fortsätter ha access och kommer in även om nätverket är nere.

## Frågor
### kan vi använda access-grupper per person?
NEJ

### kan man fjärrstyra access till dörrar?
Fråga Accessy. Delvis, om vi inte har iBeacon.

### rate limiting?
300 requests/s

### vad händer om någon byter telefonnummer?
Måste plocka bort från Organisation. Skicka ny Accessy-invite till nytt nummer vid byte i Makeradmin.

### hur fungerar pagination?
Fixat


## Inbjudan
* Invite via API
* SMS skickas till personen
* Personen får installera Accessy-appen och registrera användare i appen

## Pending / shipping
* 30 dagar måste bli 28 dagar i pending labaccess
* Nyköp blir 28 dagar
* Vi behöver avrunda nuvarande labaccesser till slutet på veckan
* Pending skeppas i slutet på varje vecka
* Behövs inget startdatum. Istället avrundas vid skeppning.
* Synkning bryr sig inte om pending, bara aktuella spans.
* Behöver kunna skeppa för specifik användare vid medlemsintroduktion


# API-anrop
## 1. Få session token

```bash
$ CLIENT_SECRET="..."
$ CLIENT_ID="..."

$ curl -s --location --request POST 'https://api.accessy.se/auth/oauth/token' --header 'Content-Type: application/json' --data-raw '{
    "audience": "https://api.accessy.se",
    "grant_type": "client_credentials",
    "client_id": "'$CLIENT_ID'",
    "client_secret": "'$CLIENT_SECRET'"
}'


{"access_token":"...","token_type":"Bearer","expires_in":"604800000"}
=> SESSION_TOKEN="$access_token"
```


## 2. Få organization ID

```bash
$ curl -s --location --request GET 'https://api.accessy.se/asset/user/organization-membership' --header 'Authorization: Bearer '$SESSION_TOKEN

[{"id":"...","userId":"...","organizationId":"...","roles":["ASSET_ADMINISTRATOR","DEVICE_ADMINISTRATOR","REALESTATE_ADMINISTRATOR","USER","ORGANIZATION_ADMINISTRATOR","DELEGATOR"]}]

=> ORG_ID="$organizationId"
```

## 3. Få lista på user ID för organisation

```bash
$ curl --location --request GET 'https://api.accessy.se/asset/admin/organization/'$ORG_ID'/user' --header 'Authorization: Bearer '$SESSION_TOKEN

{"items":[{"id":"...","msisdn":"+46...","firstName":"...","lastName":"..."},{"id":"...","msisdn":"+46...","firstName":"...","lastName":"..."},{"id":"...","msisdn":"+46...","firstName":"...","lastName":"..."},{"id":"...","msisdn":"+46...","firstName":"...","lastName":"..."},{"id":"...","firstName":"...","lastName":"..."},{"id":"...","msisdn":"+46...","firstName":"...","lastName":"..."}],"totalItems":6,"pageSize":25,"pageNumber":0,"totalPages":1}
```

## 4. Få membership ID för user