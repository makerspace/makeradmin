import React, { useState } from "react";
import Select from "react-select";
import { get } from "../gateway";
import { showError, showSuccess } from "../message";

function create_option(label) {
    return { label: label, value: label };
}

function download_blob(blob, file_name) {
    const element = document.createElement("a");
    element.href = URL.createObjectURL(blob);
    element.download = file_name;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    URL.revokeObjectURL(element.href);
}

function exportAccounting(year, month, file_name) {
    if (file_name) {
        file_name = file_name + ".si";
    } else {
        file_name = `Accounting_${year}_${month}.si`;
    }

    return get({
        url: `/webshop/download-accounting-file/${year}/${month}`,
    })
        .then((response) => {
            const blob = new Blob([atob(response.data)], {
                type: "text/plain",
            });
            download_blob(blob, file_name);
            showSuccess("Laddat ner SIE-fil för bokföring.");
        })
        .catch((error) => {
            showError(
                "<h2>Misslyckades ladda ner fil.</h2>Kunde inte kommunicera med servern: " +
                    error.message,
            );
        });
}

export default function AccountingExport() {
    let year_options = [];
    let month_options = [];
    const current_year = new Date().getFullYear();
    const current_month = new Date().getMonth() + 1;

    for (let i = current_year; i >= 2020; i--) {
        year_options.push(create_option(i));
    }
    for (let i = 1; i <= 12; i++) {
        month_options.push(create_option(i));
    }

    const [yearOption, setYearOption] = useState(create_option(current_year));
    const [monthOption, setMonthOption] = useState(
        create_option(current_month),
    );
    const [loading, setLoading] = useState(false);

    const handleExportClick = (event) => {
        event.preventDefault();
        setLoading(true);
        const promise = exportAccounting(
            yearOption.label,
            monthOption.label,
            document.getElementById("file_name").value,
        );
        promise.then(() => setLoading(false));
    };

    return (
        <div>
            <h2>Exportera SIE-fil</h2>
            <p>
                På denna sida kan du exportera transaktioner för vald period
                till en SIE-fil.
            </p>
            <form className="uk-form uk-form-stacked">
                <fieldset className="uk-margin-top">
                    <div>
                        <legend className="uk-legend">
                            Välj vilken period du vill exportera
                        </legend>
                        <label className="uk-form-label" htmlFor="year">
                            År:
                        </label>
                        <Select
                            id="year"
                            name="year"
                            className="uk-select"
                            tabIndex={1}
                            options={year_options}
                            value={yearOption}
                            onChange={(from_year) => setYearOption(from_year)}
                        />
                        <label className="uk-form-label" htmlFor="month">
                            Månad:
                        </label>
                        <Select
                            id="month"
                            name="month"
                            className="uk-select"
                            tabIndex={2}
                            options={month_options}
                            value={monthOption}
                            onChange={(month) => setMonthOption(month)}
                        />
                    </div>
                    <div>
                        <label className="uk-form-label" htmlFor="file_name">
                            File name:
                        </label>
                        <input
                            type="text"
                            tabIndex={3}
                            placeholder="Enter file name..."
                            id="file_name"
                            name="file_name"
                            className="uk-input uk-width-1-1"
                        />
                    </div>
                    <button
                        className="uk-button uk-button-primary uk-width-1-1"
                        role="button"
                        tabIndex={4}
                        style={{ marginTop: "2px" }}
                        disabled={loading}
                        onClick={handleExportClick}
                    >
                        {loading ? "Laddar..." : "Exportera"}
                    </button>
                </fieldset>
            </form>
        </div>
    );
}
