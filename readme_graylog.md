## Graylog

we are trying out graylog to gather app and system logs and send slack notifications
To generate a sha256 hashed password for the .env file run `echo -n yourpassword | shasum -a 256`

Configurations needs to be done in the web gui

First two GELF UDP inputs is configured under system/input > Inputs on port 12201 for docker and 12202 for the api.
Once that is done log events should be showing up under Search.
To configure slack notifications go to alert > notifications and create a new notification with a slack webhook. Then a filter under Alerts > Event Defenition needs to be craeted to select what alerts to send.
When creating the event defenition you can free text search in the log under filter & aggragation > search query. You can also group and filter events under Filter. Once configure, add a notification to the event.

To configure docker to be logged create /etc/docker/daemon.json

```
{
  "log-driver": "gelf",
  "log-opts": {
    "gelf-address": "udp://localhost:12201"
  }
}
```
