#
# This file doesn't really belong in the webshop, but it does share a significant amount of boilerplate
# so it is easy to just put it here.
#

from flask import Flask
import service
from service import route_helper
from typing import List, Tuple
from datetime import datetime
instance = service.create(name="Makerspace Statistics Backend", url="statistics", port=9000, version="1.0")

app = Flask(__name__)
app.register_blueprint(instance.blueprint)

# Grab the database so that we can use it inside requests
db = instance.db

@instance.route("membership/by_date", methods=["GET"], permission=None)
@route_helper
def membership_by_date_statistics ():
	return {
		"membership": spans_by_date("membership"),
		"labaccess": spans_by_date("labaccess"),
	}

def spans_by_date(span_type) -> List[Tuple[datetime,int]]:
	# Warning: doesn't accurately add datapoints when the number of members drops to zero
	# But since we know that Stockholm Makerspace will exist forever, this is an edge case that will never happen.
	query = """
	SELECT date, count(distinct(member_id)) AS labmembers
		FROM membership_spans as ms
		JOIN (
			(SELECT enddate AS date FROM membership_spans WHERE type = %s AND deleted_at IS NULL)
			UNION DISTINCT
			(SELECT DATE_ADD(enddate, INTERVAL 1 DAY) as date FROM membership_spans WHERE type = %s AND deleted_at IS NULL)
			UNION DISTINCT
			(SELECT startdate FROM membership_spans WHERE type = %s AND deleted_at IS NULL)
			UNION DISTINCT
			(SELECT DATE_SUB(startdate, INTERVAL 1 DAY) FROM membership_spans WHERE type = %s AND deleted_at IS NULL)
		) AS dates
		ON (
			ms.startdate <= dates.date AND
			dates.date <= ms.enddate
		)
		WHERE (
			ms.type = %s AND
			ms.deleted_at IS NULL
		)
		GROUP BY date
		ORDER BY date;"""

	with db.cursor() as cur:
		cur.execute(query, (span_type, span_type, span_type, span_type, span_type))
		dates: List[Tuple[datetime,int]] = cur.fetchall()

		# new_dates = []
		# for date in dates:
		# 	while len(new_dates) > 0 and round((date[0] - new_dates[-1][0]).total_seconds()/(24*3600)) > 1:
		# 		new_dates.append((new_dates[-1][0] + timedelta(days=1), new_dates[-1][1]))
		# 	new_dates.append(date)

		dates = [(date.strftime("%Y-%m-%d"), count) for (date, count) in dates]

		return dates

@instance.route("lasertime/by_month", methods=["GET"], permission=None)
@route_helper
def lasertime():
	with db.cursor() as cur:
		cur.execute("SELECT id FROM webshop_products WHERE name='Använding av Laserskärare'");
		id = cur.fetchone()
		if id is None:
			abort(500, "Kunde inte hitta laserskärningstidsprodukten")

		cur.execute("""
			SELECT DATE_FORMAT(webshop_transactions.created_at, "%%Y-%%m"), sum(webshop_transaction_contents.count) FROM webshop_transaction_contents
			INNER JOIN webshop_transactions
			ON webshop_transactions.id = webshop_transaction_contents.transaction_id
			WHERE webshop_transaction_contents.product_id=%s AND webshop_transactions.status='completed'
			GROUP BY DATE_FORMAT(webshop_transactions.created_at, "%%Y-%%m")
			""", id)
		results = cur.fetchall()
		results = [(date, int(count)) for (date, count) in results]
		return results
