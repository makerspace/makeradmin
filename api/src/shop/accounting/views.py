import multiprocessing
from datetime import date
from typing import Any

from dateutil.relativedelta import relativedelta
from flask import g
from membership.models import Member
from service.api_definition import GET, POST, WEBSHOP
from service.db import db_session
from service.error import InternalServerError
from sqlalchemy import select

from shop.accounting import service
from shop.accounting.export import do_export
from shop.accounting.models import AccountingExport, Aggregation


@service.route("/export/<int:year>/<int:month>", method=POST, permission=WEBSHOP)
def start_accounting_export_route(year: int, month: int) -> int:
    start_date = date(year=year, month=month, day=1)
    end_date = start_date + relativedelta(months=1)

    signer_member_id: int = g.user_id

    signer = db_session.get(Member, signer_member_id)
    if signer is None:
        raise ValueError(f"Member with id {signer_member_id} not found")

    e = AccountingExport(
        signer_member_id=signer_member_id,
        aggregation=Aggregation.month,
        start_date=start_date,
        end_date=end_date,
    )
    db_session.add(e)
    db_session.flush()

    created_id = e.id
    assert created_id is not None

    db_session.commit()

    job = multiprocessing.Process(target=do_export, args=(e,))
    job.start()

    return created_id


@service.route("/export/", method=GET, permission=WEBSHOP)
def list_accounting_files_route() -> list[dict[str, Any]]:
    return [f.to_dict() for f in db_session.execute(select(AccountingExport)).scalars()]


@service.route("/export/<int:export_id>", method=GET, permission=WEBSHOP)
def get_export_route(export_id: int) -> dict[str, Any]:
    export = db_session.get(AccountingExport, export_id)
    if export is None:
        raise InternalServerError(f"Accounting file with id {export_id} not found")

    return export.to_dict()
