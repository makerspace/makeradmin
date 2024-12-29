import json
import os
import re
from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Tuple

import progressbar
import requests
from bs4 import BeautifulSoup
from dataclasses_json import DataClassJsonMixin
from progressbar import ProgressBar


@dataclass
class Attendee(DataClassJsonMixin):
    name: str
    email: str
    purchaser_email: str


@dataclass
class EventTicketType(DataClassJsonMixin):
    name: str
    price: float
    max_slots: int


@dataclass
class Event(DataClassJsonMixin):
    id: int
    date: str
    name: str
    attendees: List[Attendee]
    closed: bool = False
    host: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    ticket_types: Optional[List[EventTicketType]] = None


parser = ArgumentParser()
parser.add_argument("--output", type=str, required=True, help="Output json file path")
parser.add_argument(
    "--update",
    action="store_true",
    help="Update existing data in the json file, if it exists. This is faster and can preserve more info from simplesignup if invoked regularly.",
)
parser.add_argument("--quiet", action="store_true", help="Don't print anything to stdout")
parser.add_argument("--login-cookie", required=True, help="Login cookie '_events_c_session' from SimpleSignup")

args = parser.parse_args()
output_path: str = args.output
update: bool = args.update
quiet: bool = args.quiet
cookie: str = args.login_cookie

cookies = {
    "_events_c_session": args.login_cookie,
}

all_events: List[Event] = []
if update:
    if os.path.isfile(output_path):
        with open(output_path) as f:
            all_events = Event.schema().loads(f.read(), many=True)


def scrape_attendees(event_id: int) -> Tuple[str, List[Attendee]]:
    r = requests.get(
        f"https://simplesignup.se/events/{event_id}/attendees?status=confirmed",
        cookies=cookies,
    )

    soup = BeautifulSoup(r.text, "html.parser")

    # Event name that is not truncated
    name = "".join(soup.find("h2").strings).replace("Deltagare för", "").strip()

    attendees_table = soup.find("table", id="attendees_table")

    attendees = []
    if attendees_table is not None:
        for attendee_row in attendees_table.find_all("tr")[1:]:
            fname = attendee_row.find(class_="class_2").string.strip()
            lname = attendee_row.find(class_="class_3").string.strip()
            email = attendee_row.find(class_="class_4").string.strip().lower()

            purchaser_email = attendee_row.find(class_="class_10").string.strip().lower()
            attendees.append(Attendee(name=f"{fname} {lname}", email=email, purchaser_email=purchaser_email))

    return name, attendees


def try_scrape_event_info(event: Event) -> bool:
    r = requests.get(
        f"https://simplesignup.se/events/{event.id}/edit",
        cookies=cookies,
    )
    soup = BeautifulSoup(r.text, "html.parser")
    host_input = soup.find("input", id="event_organizer")
    # May be None if the event is too old
    if host_input is None:
        return False

    event.host = host_input.get("value")

    start_date_str = soup.find("input", id="event_start_time").get("value")
    start_hour_str = (
        soup.find("select", id="event_start_time_4i").find("option", attrs={"selected": "selected"}).get("value")
    )
    start_minute_str = (
        soup.find("select", id="event_start_time_5i").find("option", attrs={"selected": "selected"}).get("value")
    )
    end_date_str = soup.find("input", id="event_end_time").get("value")
    end_hour_str = (
        soup.find("select", id="event_end_time_4i").find("option", attrs={"selected": "selected"}).get("value")
    )
    end_minute_str = (
        soup.find("select", id="event_end_time_5i").find("option", attrs={"selected": "selected"}).get("value")
    )

    start_date = datetime.strptime(f"{start_date_str} {start_hour_str}:{start_minute_str}", "%Y-%m-%d %H:%M")
    end_date = datetime.strptime(f"{end_date_str} {end_hour_str}:{end_minute_str}", "%Y-%m-%d %H:%M")
    event.start_time = start_date
    event.end_time = end_date

    event.ticket_types = []
    for ticket_row in soup.find_all(class_="ticket-type"):
        name = ticket_row.find(class_="ticket-type-name").find("input").get("value")
        if name is None:
            continue
        price = ticket_row.find(class_="ticket-type-price").find("input").get("value")
        max_slots = ticket_row.find(class_="ticket-type-max_tickets").find("input").get("value")
        # print(ticket_row)
        # print(name, price, max_slots)
        event.ticket_types.append(EventTicketType(name=name, price=float(price), max_slots=int(max_slots)))

    return True


bar = ProgressBar(max_value=progressbar.UnknownLength)
counter = 0
for page in range(1, 5):
    r = requests.get(
        f"https://simplesignup.se/events?page={page}",
        cookies=cookies,
    )
    soup = BeautifulSoup(r.text, "html.parser")
    events_list = list(soup.find_all("tr", class_="event"))
    bar.max_value = counter + len(events_list)
    for event_tr in events_list:
        counter += 1
        if not quiet:
            bar.update(counter)
        event_id = int(event_tr.find(class_="my-events-event-id").string.strip())
        date_str = event_tr.find(class_="my-events-event-date").string.strip()

        # Date format: 17 Aug, 2022
        date_obj = datetime.strptime(date_str, "%d %b, %Y").date()
        name = "".join(event_tr.find(class_="my-events-event-name").strings).strip()

        event = next((e for e in all_events if e.id == event_id), None)
        if event is None:
            event = Event(id=event_id, date=date_obj.isoformat(), name=name, attendees=[], closed=False)
            all_events.append(event)

        # Don't try to scrape again if we already know it's closed.
        # The attendees and info won't change
        if not event.closed:
            event.name, event.attendees = scrape_attendees(event.id)
            could_scrape_info = try_scrape_event_info(event)
            event.closed = not could_scrape_info

if not quiet:
    bar.finish()

with open(output_path, "w") as f:
    f.write(Event.schema().dumps(all_events, many=True))

if counter == 0:
    if not quiet:
        print("No events found")
    exit(2)
