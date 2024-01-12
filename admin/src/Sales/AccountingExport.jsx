import React from "react";
import Select from "react-select";
import { showError, showSuccess } from "../message";
import { get } from "../gateway";

class AccountingExport extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            csv_content: null,
            state: "none",
            selectedOption_from: null,
            selectedOption_to: null,
        };
    }
    exportAccounting(file_name) {
        if (
            this.state.selectedOption_from &&
            this.state.selectedOption_to &&
            Object.values(this.state.selectedOption_from)[0] <=
                Object.values(this.state.selectedOption_to)[0]
        ) {
            if (file_name) {
                file_name = file_name + ".sie";
            } else {
                file_name =
                    "Accounting_" +
                    Object.values(this.state.selectedOption_from)[0] +
                    "_" +
                    Object.values(this.state.selectedOption_to)[0] +
                    ".sie";
            }

            get({
                url:
                    "/webshop/download-accounting-file/" +
                    Object.values(this.state.selectedOption_from)[0] +
                    "/" +
                    Object.values(this.state.selectedOption_to)[0],
            })
                .then((r) => {
                    const element = document.createElement("a");
                    const file = new Blob([r.data], { type: "text/plain" });
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

    selectOptionFrom(year) {
        this.setState({ selectedOption_from: year });
    }

    selectOptionTo(year) {
        this.setState({ selectedOption_to: year });
    }

    render() {
        const { selectedOption_from, selectedOption_to } = this.state;
        let years = [];
        let current_year = new Date().getFullYear();

        for (let i = current_year; i >= 2020; i--) {
            years.push({ year: i });
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
                                    Från och med år:
                                </label>
                                <Select
                                    name="from_year"
                                    className="uk-select"
                                    tabIndex={1}
                                    options={years}
                                    value={selectedOption_from}
                                    getOptionValue={(g) => g.year}
                                    getOptionLabel={(g) => g.year}
                                    onChange={(from_year) =>
                                        this.selectOptionFrom(from_year)
                                    }
                                />
                                <label className="uk-form-label" htmlFor="">
                                    Till och med år:
                                </label>
                                <Select
                                    name="to_year"
                                    className="uk-select"
                                    tabIndex={1}
                                    options={years}
                                    value={selectedOption_to}
                                    getOptionValue={(g) => g.year}
                                    getOptionLabel={(g) => g.year}
                                    onChange={(to_year) =>
                                        this.selectOptionTo(to_year)
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
