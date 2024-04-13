import React from "react";
import Select from "react-select";
import { get } from "../gateway";
import { showError, showSuccess } from "../message";

class AccountingExport extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            csv_content: null,
            state: "none",
            selectedOption_year: null,
            selectedOption_month: null,
        };
    }
    exportAccounting(file_name) {
        if (this.state.selectedOption_year && this.state.selectedOption_month) {
            if (file_name) {
                file_name = file_name + ".si";
            } else {
                file_name =
                    "Accounting_" +
                    Object.values(this.state.selectedOption_year)[0] +
                    "_" +
                    Object.values(this.state.selectedOption_month)[0] +
                    ".si";
            }

            get({
                url:
                    "/webshop/download-accounting-file/" +
                    Object.values(this.state.selectedOption_year)[0] +
                    "/" +
                    Object.values(this.state.selectedOption_month)[0],
            })
                .then((response) => {
                    const element = document.createElement("a");
                    const file = new Blob([atob(response.data)], {
                        type: "text/plain",
                    });
                    element.href = URL.createObjectURL(file);
                    element.download = file_name;
                    document.body.appendChild(element);
                    element.click();
                    document.body.removeChild(element);
                    showSuccess("Laddat ner SIE-fil för bokföring.");
                })
                .catch((error) => {
                    showError(
                        "<h2>Misslyckades ladda ner fil.</h2>Kunde inte kommunicera med servern: " +
                            error.message,
                    );
                });
        } else {
            showError(
                "<h2>Failed</h2>You missed entering to and from years, or you have mixed up the order of years",
            );
        }
    }

    selectOptionYear(year) {
        this.setState({ selectedOption_year: year });
    }

    selectOptionMonth(month) {
        this.setState({ selectedOption_month: month });
    }

    render() {
        const { selectedOption_year, selectedOption_month } = this.state;
        let years = [];
        let months = [];
        let current_year = new Date().getFullYear();

        for (let i = current_year; i >= 2020; i--) {
            years.push({ year: i });
        }
        for (let i = 1; i <= 12; i++) {
            months.push({ month: i });
        }

        return (
            <div>
                <div>
                    <h2>Exportera SIE-fil</h2>
                    <p>
                        På denna sida kan du exportera transaktioner för vald
                        period till en SIE-fil.
                    </p>
                    <form className="uk-form uk-form-stacked">
                        <fieldset className="uk-margin-top">
                            <div>
                                <legend>
                                    <i className="uk-icon-shopping-cart" /> Välj
                                    vilken period du vill exportera
                                </legend>
                                <label className="uk-form-label" htmlFor="">
                                    År:
                                </label>
                                <Select
                                    name="year"
                                    className="uk-select"
                                    tabIndex={1}
                                    options={years}
                                    value={selectedOption_year}
                                    getOptionValue={(g) => g.year}
                                    getOptionLabel={(g) => g.year}
                                    onChange={(from_year) =>
                                        this.selectOptionYear(from_year)
                                    }
                                />
                                <label className="uk-form-label" htmlFor="">
                                    Månad:
                                </label>
                                <Select
                                    name="month"
                                    className="uk-select"
                                    tabIndex={1}
                                    options={months}
                                    value={selectedOption_month}
                                    getOptionValue={(g) => g.month}
                                    getOptionLabel={(g) => g.month}
                                    onChange={(month) =>
                                        this.selectOptionMonth(month)
                                    }
                                />
                            </div>
                            <div>
                                <label className="uk-form-label" htmlFor="">
                                    File name:
                                </label>
                                <input
                                    type="text"
                                    placeholder="Enter file name..."
                                    id="file_name"
                                    name="file_name"
                                />
                            </div>

                            <div
                                className="uk-button uk-button-primary"
                                role="button"
                                style={{ marginTop: "2px" }}
                                onClick={() =>
                                    this.exportAccounting(
                                        document.getElementById("file_name")
                                            .value,
                                    )
                                }
                            >
                                Exportera SIE-fil för vald period
                                {this.state.state === "loading" ? "..." : ""}
                            </div>
                        </fieldset>
                    </form>
                </div>
            </div>
        );
    }
}

export default AccountingExport;
