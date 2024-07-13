import React, { useState } from "react";
import Select from "react-select";
import { get } from "../gateway";
import { showError, showSuccess } from "../message";

function AccountingExport() {
    const [yearOption, setYear] = useState(null);
    const [monthOption, setMonth] = useState(null);

    let year_options = [];
    let month_options = [];
    let current_year = new Date().getFullYear();

    for (let i = current_year; i >= 2020; i--) {
        year_options.push({ value: i, label: i });
    }
    for (let i = 1; i <= 12; i++) {
        month_options.push({ value: i, label: i });
    }

    const exportAccounting = (file_name) => {
        if (yearOption && monthOption) {
            if (file_name) {
                file_name = file_name + ".si";
            } else {
                file_name =
                    "Accounting_" +
                    Object.values(yearOption)[0] +
                    "_" +
                    Object.values(monthOption)[0] +
                    ".si";
            }

            get({
                url:
                    "/webshop/download-accounting-file/" +
                    Object.values(yearOption)[0] +
                    "/" +
                    Object.values(monthOption)[0],
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
    };

    return (
        <div>
            <div>
                <h2>Exportera SIE-fil</h2>
                <p>
                    På denna sida kan du exportera transaktioner för vald period
                    till en SIE-fil.
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
                                options={year_options}
                                value={yearOption}
                                onChange={(from_year) => setYear(from_year)}
                            />
                            <label className="uk-form-label" htmlFor="">
                                Månad:
                            </label>
                            <Select
                                name="month"
                                className="uk-select"
                                tabIndex={1}
                                options={month_options}
                                value={monthOption}
                                onChange={(month) => setMonth(month)}
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

                        <button
                            className="uk-button uk-button-primary"
                            role="button"
                            style={{ marginTop: "2px" }}
                            onClick={(event) => {
                                event.preventDefault();
                                exportAccounting(
                                    document.getElementById("file_name").value,
                                );
                            }}
                        >
                            Exportera SIE-fil för vald period
                        </button>
                    </fieldset>
                </form>
            </div>
        </div>
    );
}

export default AccountingExport;
