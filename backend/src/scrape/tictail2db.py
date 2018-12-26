#!/usr/bin/env python3
import sys
import json
from decimal import Decimal
import re
import os

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import backend_service

db, gateway, debug = backend_service.read_config()
db.connect()

data = json.loads(open("tictail.json", encoding="utf-8").read())
seen_names = set()

for item in data:
    name = item["name"].strip()
    suffix = item["suffix"].strip()
    if name + suffix in seen_names:
        print("Skipping duplicate")
        continue

    seen_names.add(name + suffix)
    image = item["image"].strip()
    description = item["description"]
    price = Decimal(item["price"])
    category = item["category"]

    description = re.sub("\n"," ", description)
    # description = re.sub("<br/>","\n", description)
    description = re.sub("<p>","\n<p>", description)
    description = re.sub("</p>","</p>\n\n", description)
    description = re.sub("\n\n+","\n\n", description)
    description = re.sub(" +"," ", description)
    description = description.strip()

    name = name + " " + suffix
    name = name.strip()
    unit = "st"

    if name.endswith(" 100g"):
        unit = "g"
        price /= 100
        name = name[:-5]

    if name.endswith(" 100mm"):
        unit = "mm"
        price /= 100
        name = name[:-6]

    if name == "Använding av Laserskärare":
        unit = "s"

    with db.cursor() as cur:
        cur.execute("SELECT id FROM webshop_product_categories WHERE name=%s", (category,))
        cat_id = cur.fetchone()
        if cat_id is None:
            cur.execute("INSERT INTO webshop_product_categories (name) VALUES(%s)", (category,))

        cur.execute("SELECT id FROM webshop_product_categories WHERE name=%s", (category,))
        cat_id = cur.fetchone()
        assert(cat_id is not None)
        cur.execute("INSERT INTO webshop_products (name,category_id,description,unit,price) VALUES(%s,%s,%s,%s,%s)", (name,cat_id[0],description,unit,price))


with db.cursor() as cur:
    cur.execute("SELECT id FROM webshop_products WHERE name = 'Medlemsavgift'")
    id = cur.fetchone()[0]

    cur.execute(f"INSERT INTO  webshop_product_actions (product_id, action_id, value) VALUES ({id}, 1, 365), ({id + 1}, 2, 30), ({id + 2}, 1, 365), ({id + 2}, 2, 90)")
