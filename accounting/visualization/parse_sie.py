#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import os
import argparse
import shlex
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from dataclasses_json import config
from dataclasses_json.api import DataClassJsonMixin
from marshmallow import fields


@dataclass
class SIEObjekt(DataClassJsonMixin):
    type: int
    code: str
    name: str


@dataclass
class SIEVerificationLine(DataClassJsonMixin):
    account: int
    objects: List[str]
    amount: Decimal
    date: datetime = field(
        metadata=config(
            encoder=datetime.isoformat, decoder=datetime.fromisoformat, mm_field=fields.DateTime(format="iso")
        )
    )
    description: str


@dataclass
class SIEVerification(DataClassJsonMixin):
    series: str
    id: int
    date: datetime = field(
        metadata=config(
            encoder=datetime.isoformat, decoder=datetime.fromisoformat, mm_field=fields.DateTime(format="iso")
        )
    )
    description: str
    lines: List[SIEVerificationLine]


@dataclass
class DateRange:
    start: date = field(
        metadata=config(encoder=date.isoformat, decoder=date.fromisoformat, mm_field=fields.Date(format="iso"))
    )
    end: date = field(
        metadata=config(encoder=date.isoformat, decoder=date.fromisoformat, mm_field=fields.Date(format="iso"))
    )


@dataclass
class SIEFile(DataClassJsonMixin):
    gen: Optional[str] = None
    currency: Optional[str] = None
    program: Optional[str] = None
    format: Optional[str] = None
    orgnr: Optional[str] = None
    filename: Optional[str] = None
    date_range: Optional[DateRange] = None
    # Incoming balances for each account.
    # Indexed by relative year (0 = current year)
    incoming_balances: Dict[int, Dict[int, Decimal]] = field(default_factory=lambda: {-1: dict(), 0: dict(), 1: dict()})
    # Outgoing balances for each account.
    # Indexed by relative year (0 = current year)
    outgoing_balances: Dict[int, Dict[int, Decimal]] = field(default_factory=lambda: {-1: dict(), 0: dict(), 1: dict()})
    accounts: Dict[int, str] = field(default_factory=dict)
    dimensions: Dict[int, str] = field(default_factory=dict)
    objects: List[SIEObjekt] = field(default_factory=list)
    verifications: List[SIEVerification] = field(default_factory=list)


def main():
    parser = argparse.ArgumentParser(description="Parse SIE file format")
    parser.add_argument("--filename", required=True, nargs="+")
    parser.add_argument("--encoding", default="cp850", choices=["cp850", "latin-1", "utf-8", "windows-1252"])

    args = parser.parse_args()

    for inputfile in args.filename:
        print(parse(inputfile, args.encoding))


def parse(filepath: str, encoding: str = "cp850") -> SIEFile:
    attribute_dims = dict()

    siefile = SIEFile()

    with open(filepath, "rb") as f:
        content = f.read().decode(encoding).split("\n")
        for l in range(0, len(content)):
            line = content[l]
            if not line.startswith("#") or len(line.split(" ")) == 0:
                continue
            label, text, parts = parse_line(line)

            if label == "VALUTA":
                siefile.currency = parts[0]
            if label == "GEN":
                siefile.gen = parts[0]
            if label == "FNAMN":
                siefile.filename = parts[0]
            if label == "KONTO":
                siefile.accounts[int(parts[0])] = parts[1]
            if label == "DIM":
                attribute_dims[int(parts[0])] = parts[1]
            if label == "IB":
                (year, account, amount) = parts
                siefile.incoming_balances[int(year)][int(account)] = Decimal(amount)
            if label == "UB":
                (year, account, amount) = parts
                siefile.outgoing_balances[int(year)][int(account)] = Decimal(amount)
            if label == "OBJEKT":
                siefile.objects.append(SIEObjekt(type=int(parts[0]), code=parts[1], name=parts[2]))
            if label == "RAR":
                if int(parts[0]) == 0:
                    siefile.date_range = DateRange(
                        datetime.strptime(parts[1], "%Y%m%d").date(), datetime.strptime(parts[2], "%Y%m%d").date()
                    )
            if label == "VER":
                series = parts[0]
                verno = parts[1]
                verdate = datetime.strptime(parts[2], r"%Y%m%d")
                if len(parts) > 3:
                    vertext = parts[3]
                else:
                    vertext = ""
                l, vers = parse_ver(content, l, vertext, verdate, verno)
                siefile.verifications.append(
                    SIEVerification(series=series, id=verno, date=verdate, description=vertext, lines=vers)
                )

    for year in [-1, 0, 1]:
        for account in siefile.outgoing_balances[year].keys():
            if account not in siefile.incoming_balances[year]:
                siefile.incoming_balances[year][account] = Decimal(0)

        for account in siefile.incoming_balances[year].keys():
            if account not in siefile.outgoing_balances[year]:
                siefile.outgoing_balances[year][account] = Decimal(0)

    return siefile


def parse_line(line):
    if not line.startswith("#") or len(line.split(" ")) == 0:
        return False, False, False
    parts = [s for s in shlex.split(line.replace("{", '"').replace("}", '"'))]
    label = parts[0].upper()[1:]
    text = " ".join(parts[1:])
    return label, text, parts[1:]


def parse_ver(content, line, default_vertext, default_verdate, verno) -> Tuple[int, List[SIEVerificationLine]]:
    vers = list()
    if content[line + 1].startswith("{"):
        line = line + 2
        while not content[line].startswith("}"):
            label, text, parts = parse_line(content[line].strip())
            # print("label: %s text: %s parts: %s" % (label, text, parts))
            kst = ""
            proj = ""
            account = int(parts[0])
            p = parts[1]
            amount = Decimal(parts[2])
            if len(parts) > 3:
                verdate = datetime.strptime(parts[3], r"%Y%m%d")
            else:
                verdate = default_verdate
            if len(parts) > 4:
                vertext = parts[4]
            else:
                vertext = default_vertext

            objects = []
            if len(p.split(" ")) > 0 and p.split(" ")[0] == "1":
                kst = p.split(" ")[1]
                objects.append(kst)

            if len(p.split(" ")) > 2 and p.split(" ")[2] == "6":
                proj = p.split(" ")[3]

            vers.append(
                SIEVerificationLine(account=account, amount=amount, date=verdate, description=vertext, objects=objects)
            )
            line = line + 1

    return line, vers


if __name__ == "__main__":
    main()
