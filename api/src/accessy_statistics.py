import collections
from datetime import datetime, timedelta

from multiaccessy.accessy import accessy_session, Access
from service.config import config


ACCESSY_SESSION_TOKEN = config.get("ACCESSY_SESSION_TOKEN")
accessy_session.session_token = ACCESSY_SESSION_TOKEN
accessy_session.session_token_token_expires_at = datetime.now() + timedelta(days=1)


doors = accessy_session.get_all_doors()
accesses: list[Access] = []
for door in doors:
    accesses.extend(accessy_session.get_all_accesses(door))


accesses_per_door = collections.Counter(a.door.name for a in accesses)
print(f"Accesses per door: {accesses_per_door}")

accesses_per_date = collections.Counter(a.dt.date() for a in accesses)
print(f"Accesses per date: {accesses_per_date}")

weekday_lookup = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
accesses_per_day = collections.Counter(weekday_lookup[a.dt.date().weekday()] for a in accesses)
print(f"Accesses per day: {accesses_per_day}")

people_accesses_per_date = collections.defaultdict(lambda: collections.Counter())
for access in accesses:
    people_accesses_per_date[access.dt.date()].update({access.name: 1})
print(f"People accesses per date {people_accesses_per_date}")

unique_people_per_date = {d: len(people_accesses_per_date[d].keys()) for d in people_accesses_per_date.keys()}
print(f"Unique people per date {unique_people_per_date}")

people_accesses_per_day = collections.defaultdict(lambda: collections.Counter())
for access in accesses:
    people_accesses_per_day[weekday_lookup[access.dt.weekday()]].update({access.name: 1})
print(f"People accesses per day {people_accesses_per_day}")

unique_people_per_day = {d: len(people_accesses_per_day[d].keys()) for d in people_accesses_per_day.keys()}
print(f"Unique people per day {unique_people_per_day}")
