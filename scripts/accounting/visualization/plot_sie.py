import argparse
import datetime
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import parse_sie
import seaborn as sns
from matplotlib.ticker import FuncFormatter

INCOME_ACCOUNTS = [
    1934,
    3893,
    # From the accounting_place.csv file
    3010,
    3011,
    3012,
    3013,
    3014,
    3015,
    3020,
    3031,
    3032,
    3050,
    3890,
    3891,
    3892,
    3993,
]
BANK_ACCOUNTS = [1930, 1933, 1935, 1936, 1938, 2407, 2409]
IGNORE_ACCOUNTS = [2069, 1229, 7832]

# Sum all expenses for x[0] and add one item for each month which is the montly average with the label x[1]
SPREAD_OUT_EVENLY_OVER_YEAR = [("Städning - lokalkostnader", "Städning"), ("Lokalhyra", "Lokalhyra")]


def date2float(date: pd.Timestamp) -> float:
    return date.year * 12 + (date.month - 1) + (date.day - 1) / date.days_in_month


@dataclass
class PlottingInput:
    expenses_by_month: List[List[Tuple[str, Decimal]]]
    incomes_by_month: List[List[Tuple[str, Decimal]]]
    months: List[datetime.datetime]
    accounts_by_date: List[Tuple[datetime.datetime, Dict[int, Decimal]]]
    expenses_by_room: Dict[str, Decimal]
    expenses_by_account: Dict[str, Decimal]
    incomes_by_account: Dict[str, Decimal]


def average_expenses(sie: parse_sie.SIEFile):
    """
    Some expenses are known to be per-month, but the invoices may not always be paid exactly once per month.
    This method will average out those expenses for visualization purposes, so that they seem to be paid exactly once per month.
    """
    year = sie.date_range.start.year
    name2account = {v: k for (k, v) in sie.accounts.items()}
    spread_accounts = {name2account[k]: {} for (k, _) in SPREAD_OUT_EVENLY_OVER_YEAR}
    toDelete = []
    for ver in sie.verifications:
        for line in ver.lines:
            if line.account in spread_accounts:
                assert line.amount > 0
                assert len(ver.lines) == 2
                for line2 in ver.lines:
                    if line2.account not in spread_accounts[line.account]:
                        spread_accounts[line.account][line2.account] = Decimal(0)
                    spread_accounts[line.account][line2.account] += line2.amount
                    if line2.account in sie.outgoing_balances[0]:
                        sie.outgoing_balances[0][line2.account] -= line2.amount
                # spread_accounts[line.account] += line.amount
                toDelete.append(ver)
                break

    # for ver in toDelete:
    #     for line in ver.lines:
    #         if line.account in sie.outgoing_balances[0]:
    #             sie.outgoing_balances[0][line.account] -= line.amount

    sie.verifications = [v for v in sie.verifications if v not in toDelete]

    for (account, total_accounts), (_, description) in zip(spread_accounts.items(), SPREAD_OUT_EVENLY_OVER_YEAR):
        for m in range(0, 12):
            d = datetime.datetime(year=year, month=m + 1, day=1)
            sie.verifications.append(
                parse_sie.SIEVerification(
                    series="",
                    id=0,
                    date=d,
                    description=description,
                    lines=[
                        parse_sie.SIEVerificationLine(account, [], Decimal(value / 12), d, description)
                        for account, value in total_accounts.items()
                    ],
                )
            )
            for account, value in total_accounts.items():
                if account in sie.outgoing_balances[0]:
                    sie.outgoing_balances[0][account] += Decimal(value / 12)
            # sie.outgoing_balances[0][1930] -= v


def process_sie(sie: parse_sie.SIEFile) -> PlottingInput:
    year = sie.date_range.start.year
    verifications = sorted(sie.verifications, key=lambda x: x.date)
    accounts_by_date = []
    accounts = sie.incoming_balances[0].copy()
    object2name = {obj.code: obj.name for obj in sie.objects}
    date = datetime.date(year=year, month=1, day=1)
    expenses_by_month = [[]]
    incomes_by_month = [[]]
    expenses_by_room = {obj.name: Decimal(0) for obj in sie.objects}
    expenses_by_account: Dict[str, Decimal] = {}
    incomes_by_account: Dict[str, Decimal] = {}
    months = [date]
    for ver in verifications:
        if any(line.account in IGNORE_ACCOUNTS for line in ver.lines):
            continue

        while ver.date.date() > date:
            accounts_by_date.append((date, accounts.copy()))
            date += datetime.timedelta(days=1)
            if date.month != months[-1].month:
                expenses_by_month.append([])
                incomes_by_month.append([])
                months.append(date)

        for line in ver.lines:
            if line.account not in accounts:
                accounts[line.account] = 0

            accounts[line.account] += line.amount

            if line.account in INCOME_ACCOUNTS:
                # Note: amount in sie file will be the negative income
                incomes_by_month[-1].append((sie.accounts[line.account], -line.amount))

                if line.account not in incomes_by_account:
                    incomes_by_account[line.account] = Decimal(0)
                incomes_by_account[line.account] += line.amount
            elif line.account in BANK_ACCOUNTS:
                pass
            else:
                if line.account not in expenses_by_account:
                    expenses_by_account[line.account] = Decimal(0)
                expenses_by_account[line.account] += line.amount

                if len(line.objects) > 0:
                    assert len(line.objects) == 1
                    name = object2name[line.objects[0]]
                    expenses_by_month[-1].append((name, line.amount))
                    expenses_by_room[name] += line.amount
                else:
                    expenses_by_month[-1].append((sie.accounts[line.account], line.amount))

    # Double check our math
    for account, expected_value in sie.outgoing_balances[0].items():
        if account in IGNORE_ACCOUNTS:
            continue

        if account in accounts:
            assert accounts[account] == expected_value
        else:
            assert expected_value == 0, (
                f"Expected outgoing balance for account {account} to be 0, but found {expected_value}"
            )

    return PlottingInput(
        expenses_by_month=expenses_by_month,
        incomes_by_month=incomes_by_month,
        accounts_by_date=accounts_by_date,
        expenses_by_room=expenses_by_room,
        expenses_by_account=expenses_by_account,
        incomes_by_account=incomes_by_account,
        months=months,
    )


def per_month_stacked_plot(
    ax: plt.Axes, months: List[pd.Timestamp], value_by_month: List[List[Tuple[str, Decimal]]], ylabel: str
):
    unique_labels = list(set([x[0] for items in value_by_month for x in items]))
    sum_and_name = [
        (sum(x[1] for month_data in value_by_month for x in month_data if x[0] == key), key) for key in unique_labels
    ]
    # Sort to find the top expenses, but always sort unspecified expenses last
    sum_and_name.sort(reverse=True, key=lambda x: 0 if x[1] == "Kostnader ospec" else x[0])
    topNexpenses = [x[1] for x in sum_and_name[0:5]]

    colors = sns.color_palette("deep")

    # Sum the incomes/expenses per label and per month
    month_sums = []
    for i, tp in enumerate(topNexpenses):
        sum_per_month = [sum(exp[1] for exp in month_expenses if exp[0] == tp) for month_expenses in value_by_month]
        month_sums.append((tp, np.array(sum_per_month)))

    sum_per_month = [
        sum(exp[1] for exp in month_expenses if exp[0] not in topNexpenses) for month_expenses in value_by_month
    ]
    month_sums.append(("Övrigt", np.array(sum_per_month)))

    # For display, it looks nicer in the reverse order (largest expenses at the bottom, "Övrigt" at the top)
    month_sums.reverse()

    # Seaborn doesn't have a good stacked bar chart functionality.
    # So what we have to do is to plot several bar charts on top of each other.
    # This means that the first bar chart must have a height equal to the sum of all N charts.
    # The next one should have the sum of the last N-1 charts, etc.
    for i in range(0, len(month_sums)):
        label = month_sums[i][0]
        month_sums[i] = (label, sum(month_sums[j][1] for j in range(i, len(month_sums))))

    month_indices = list(range(len(months)))
    for i, (label, sum_per_month) in enumerate(month_sums):
        sns.barplot(x=month_indices, y=sum_per_month, label=label, alpha=1.0, color=colors[i], ax=ax)

    ax.legend()
    sns.despine(ax=ax, top=True, right=True)

    x_dates = [x.strftime(r"%b %Y") for x in months]

    # Draw nice lines *around* the boxes.
    # These can nicely line up with a separate line plot
    ax.xaxis.set_ticks([x - 0.5 for x in range(len(x_dates) + 1)], minor=False)
    ax.xaxis.set_ticklabels(["" for _ in range(len(x_dates) + 1)], minor=False)

    ax.xaxis.set_ticks([x for x in range(len(x_dates))], minor=True)
    ax.xaxis.set_ticklabels(x_dates, rotation=45, ha="right", minor=True)
    ax.grid(True, which="major")
    ax.set_ylabel(ylabel)


def ellipsis(s: str, threshold: int) -> str:
    if len(s) > threshold:
        return s[: threshold - 3] + "..."
    else:
        return s


def main():
    parser = argparse.ArgumentParser(description="Plot economy graphs")
    parser.add_argument(
        "--sie",
        help="Path to the input SIE file. Can be exported from your favorite accounting software.",
        required=True,
    )

    args = parser.parse_args()
    sie = parse_sie.parse(args.sie)

    # for d in [datetime.datetime(year=2021, month=6, day=1), datetime.datetime(year=2021, month=7, day=1), datetime.datetime(year=2021, month=8, day=1), datetime.datetime(2021, 9, 1), datetime.datetime(2021, 10, 1)]:
    #     sie.verifications.append(parse_sie.SIEVerification(series="", id=0, date=d, description="Hyra", lines=[
    #         parse_sie.SIEVerificationLine(1930, [], -Decimal(21982), d, ""),
    #         parse_sie.SIEVerificationLine(5010, [], Decimal(21982), d, ""),
    #     ]))
    #     sie.outgoing_balances[0][1930] -= Decimal(21982)
    #     # sie.outgoing_balances[0][5010] += 21982

    # for m in range(0,12):
    #     d = datetime.datetime(year=2021, month=m+1, day=1)
    #     v = Decimal(200000/12)
    #     sie.verifications.append(parse_sie.SIEVerification(series="", id=0, date=d, description="Sparande", lines=[
    #         parse_sie.SIEVerificationLine(1930, [], -v, d, "Sparande"),
    #         parse_sie.SIEVerificationLine(1920, [], v, d, "Sparande"),
    #     ]))
    #     sie.outgoing_balances[0][1930] -= v

    # TRANS 1930 {} -21982.00 20210527 "1071700353S Theinnovationgrowhousest"
    # TRANS 5010 {} 21982.00 20210527 "1071700353S Theinnovationgrowhousest"
    average_expenses(sie)
    input = process_sie(sie)

    data = pd.DataFrame(
        [sum(x[1][account] for account in BANK_ACCOUNTS) for x in input.accounts_by_date],
        [pd.Timestamp(x[0]) for x in input.accounts_by_date],
        columns=["amount"],
    )

    sns.set_theme(style="whitegrid")
    sns.set_style("whitegrid")

    currency_formatter = FuncFormatter(lambda p, _: f"{p / 1000:.0f}k")

    months = [pd.Timestamp(m) for m in input.months]
    month_subset = data["amount"][months]
    data = data.reset_index()
    month_subset = month_subset.reset_index()

    convert = data.copy()
    d0 = date2float(months[0])
    convert["index"] = [date2float(x) - d0 for x in data["index"]]
    # Offset by 0.5 to make them centered over the boxplot months correctly
    convert["index"] -= 0.5

    fig, axs = plt.subplots(3, 2, figsize=(12, 6), squeeze=False)
    ax0: plt.Axes = axs[0, 0]
    axs[1, 0].sharex(ax0)
    axs[2, 0].sharex(axs[1, 0])
    axs[2, 0].sharey(axs[1, 0])

    sns.lineplot(x=convert["index"], y=convert["amount"], palette="tab10", linewidth=2.5, ax=ax0)
    ax0.set_ylabel("Bankkonto + Sparkonto [kr]")
    ax0.set_xlabel("")
    ax0.set_ylim([0, None])
    sns.despine(ax=ax0, top=True, right=True)
    # Remove month names at the bottom
    # ax0.tick_params(axis='x', which='both', labelbottom=False)
    ax0.yaxis.set_major_formatter(currency_formatter)
    ax0.tick_params(axis="x", which="both", rotation=45)
    # ax0.xaxis.set_ticklabels(ax0.xaxis.get_ticklabels(minor=True), rotation=45, ha='right', minor=True)

    per_month_stacked_plot(axs[1, 0], months, input.expenses_by_month, "Utgifter [kr]")
    axs[1, 0].yaxis.set_major_formatter(currency_formatter)
    per_month_stacked_plot(axs[2, 0], months, input.incomes_by_month, "Inkomster [kr]")
    axs[2, 0].yaxis.set_major_formatter(currency_formatter)
    print("Inkomster per konto")
    sorted_incomes = sorted(input.incomes_by_account.items(), key=lambda x: x[1], reverse=True)
    print("\n".join([f"\t{sie.accounts[k]}\t{-v}" for k, v in sorted_incomes]))

    ax2 = axs[0, 1]
    sns.barplot(y=list(input.expenses_by_room.keys()), x=list(input.expenses_by_room.values()), ax=ax2)
    sns.despine(ax=ax2, right=True, top=True)
    ax2.set_xlabel("Utgifter [kr]")
    ax2.set_title("Utgifter per rum")
    print("Utgifter per rum")
    print("\n".join([f"\t{k}\t{v}" for k, v in input.expenses_by_room.items()]))

    ax2 = axs[1, 1]
    sorted_expenses = sorted(input.expenses_by_account.items(), key=lambda x: x[1], reverse=True)
    top_k = sorted_expenses[:10]
    bottom = sorted_expenses[10:]
    top_k = [(ellipsis(sie.accounts[k], 30), v) for (k, v) in top_k]
    top_k.append(("Övrigt", sum([b[1] for b in bottom])))
    sns.barplot(y=[x[0] for x in top_k], x=[x[1] for x in top_k], ax=ax2)
    sns.despine(ax=ax2, right=True, top=True)
    ax2.set_xlabel("Utgifter [kr]")
    ax2.set_title("Utgifter per konto")
    print("Utgifter per konto")
    print("\n".join([f"\t{sie.accounts[k]}\t{v}" for k, v in sorted_expenses]))

    ax2 = axs[2, 1]
    for account in BANK_ACCOUNTS:
        print(sie.accounts[account], sie.incoming_balances[0][account], sie.outgoing_balances[0][account])

    sns.barplot(
        x=[sie.date_range.start.year],
        y=[sum(sie.outgoing_balances[0][c] - sie.incoming_balances[0][c] for c in BANK_ACCOUNTS)],
    )
    ax2.set_ylabel("Resultat [kr]")
    ax2.set_title(f"Resultat {sie.date_range.start.year}")

    plt.tight_layout()
    plt.subplots_adjust(wspace=0.267, hspace=0.283)
    plt.show()


if __name__ == "__main__":
    main()
