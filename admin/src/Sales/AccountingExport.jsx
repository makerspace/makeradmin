import React, { useEffect, useId, useState } from "react";
import Select from "react-select";
import UIkit from "uikit";
import Icon from "../Components/icons";
import { get, post } from "../gateway";
import useModel from "../Hooks/useModel";
import Member from "../Models/Member";

function create_option(label) {
    return { label: label, value: label };
}

function download_text(content, file_name) {
    const blob = new Blob([content], {
        type: "text/plain",
    });
    const element = document.createElement("a");
    element.href = URL.createObjectURL(blob);
    element.download = file_name;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    URL.revokeObjectURL(element.href);
}

function downloadAccounting(accounting_export) {
    download_text(
        accounting_export.content,
        format_date(new Date(accounting_export.start_date)) +
            "_" +
            format_date(new Date(accounting_export.end_date)) +
            "_" +
            accounting_export.aggregation +
            ".sie",
    );
}

function exportAccounting(year, month) {
    return post({
        url: `/webshop/accounting/export/${year}/${month}`,
        expectedDataStatus: "ok",
    }).then(({ data }) => {
        UIkit.notification(`Export #${data} startad`, {
            timeout: 1000,
            status: "success",
        });
    });
}

function StartExportForm() {
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
        const promise = exportAccounting(yearOption.label, monthOption.label);
        promise.finally(() => setLoading(false));
    };

    return (
        <form className="uk-form-stacked">
            <fieldset className="uk-margin-top">
                <legend className="uk-legend">
                    Välj vilken period du vill exportera
                </legend>
                <label className="uk-form-label" htmlFor="year">
                    År:
                </label>
                <Select
                    id="year"
                    name="year"
                    className="uk-width-1-1"
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
                    className="uk-width-1-1"
                    tabIndex={2}
                    options={month_options}
                    value={monthOption}
                    onChange={(month) => setMonthOption(month)}
                />
                <button
                    className="uk-button uk-button-primary uk-width-1-1"
                    role="button"
                    tabIndex={4}
                    disabled={loading}
                    onClick={handleExportClick}
                >
                    {loading ? "Laddar..." : "Starta export"}
                </button>
            </fieldset>
        </form>
    );
}

function status_to_emoji(status) {
    if (status === "completed") {
        return "✅";
    }
    if (status === "pending") {
        return "⏳";
    }
    return "❌";
}

function OutputViewer({ status, content }) {
    return (
        <>
            <label className="uk-form-label" htmlFor="content">
                {status === "completed" ? "Resultat" : "Felmeddelande"}
            </label>
            <textarea
                readOnly
                rows={10}
                id="content"
                className={
                    "uk-textarea uk-width-1-1 uk-resize-vertical" +
                    (status === "completed" ? "" : " error")
                }
                disabled
                value={content}
            ></textarea>
        </>
    );
}

function Field({ label, value }) {
    const id = useId(label);
    return (
        <>
            <label className="uk-form-label" htmlFor={id}>
                {label}:
            </label>
            <input
                id={id}
                className="uk-input uk-width-1-1"
                disabled
                value={value}
            />
        </>
    );
}

function Signer({ member_id }) {
    const member = useModel(Member, member_id);

    return (
        <>
            <label className="uk-form-label" htmlFor="signer">
                Signerad av:
            </label>
            <input
                id="signer"
                className="uk-input uk-width-1-1"
                disabled
                value={member ? member.toString() : `${member_id}`}
            />
        </>
    );
}

function format_time(dt) {
    const hour = String(dt.getHours()).padStart(2, "0");
    const minute = String(dt.getMinutes()).padStart(2, "0");
    return `${hour}:${minute}`;
}

function format_date(dt, include_time = false) {
    const year = dt.getFullYear();
    const month = String(dt.getMonth() + 1).padStart(2, "0");
    const day = String(dt.getDate()).padStart(2, "0");

    if (include_time) {
        return `${year}-${month}-${day} ${format_time(dt)}`;
    }

    return `${year}-${month}-${day}`;
}

function Preview({ accounting_export }) {
    return (
        <>
            <Signer member_id={accounting_export.signer_member_id} />
            <Field
                label="Status"
                value={
                    accounting_export.status === "completed"
                        ? "Klar"
                        : accounting_export.status === "pending"
                          ? "Pågående"
                          : "Exporten misslyckades"
                }
            />
            <div className="uk-grid">
                <div className="uk-width-1-2">
                    <Field
                        label="Start på period"
                        value={format_date(
                            new Date(accounting_export.start_date),
                        )}
                    />
                </div>
                <div className="uk-width-1-2">
                    <Field
                        label="Slut på period"
                        value={format_date(
                            new Date(accounting_export.end_date),
                        )}
                    />
                </div>
            </div>
            <Field
                label="Skapad"
                value={format_date(
                    new Date(accounting_export.created_at),
                    true,
                )}
            />
            <Field label="Aggregering" value={accounting_export.aggregation} />
            {accounting_export.content && (
                <OutputViewer
                    status={accounting_export.status}
                    content={accounting_export.content || ""}
                />
            )}
        </>
    );
}

function DownloadExportForm() {
    const [exportedRanges, setExportedRanges] = useState([]);
    const [selectedExport, setSelectedExport] = useState(null);
    const id = useId();

    const fetchExportedRanges = async () => {
        const response = await get({
            url: "/webshop/accounting/export/",
        });

        const data_most_recent_first = response.data.sort((a, b) =>
            new Date(a.updated_at).getTime() < new Date(b.updated_at).getTime()
                ? 1
                : -1,
        );
        const options = data_most_recent_first.map((d) => {
            const start_date = format_date(new Date(d.start_date));
            const end_date = format_date(new Date(d.end_date));
            return {
                label: `${d.id} ${status_to_emoji(d.status)} ${
                    d.status
                } (${start_date} - ${end_date})`,
                value: d,
            };
        });
        setExportedRanges(options);
    };

    useEffect(() => {
        fetchExportedRanges();
    }, []);

    const can_download =
        selectedExport && selectedExport.status === "completed";

    return (
        <form className="uk-form-stacked">
            <fieldset className="uk-margin-top">
                <legend className="uk-legend">
                    Ladda ner exporterade perioder
                </legend>
                <label className="uk-form-label" htmlFor={id}>
                    Exporter:
                </label>
                <div className="uk-grid">
                    <div className="uk-width-2-3">
                        <Select
                            id={id}
                            name="Export"
                            className={"uk-width-1-1"}
                            tabIndex={5}
                            options={exportedRanges}
                            selected={selectedExport}
                            onChange={(selected) =>
                                setSelectedExport(selected.value)
                            }
                            onMenuOpen={fetchExportedRanges}
                        />
                    </div>
                    <div className="uk-width-1-3">
                        <button
                            className="uk-button uk-button-primary uk-width-1-1"
                            role="button"
                            disabled={!can_download}
                            tabIndex={6}
                            onClick={(event) => {
                                event.preventDefault();
                                downloadAccounting(selectedExport);
                            }}
                        >
                            <Icon icon="cloud-download" /> Ladda ner
                        </button>
                    </div>
                </div>
                {selectedExport && (
                    <Preview accounting_export={selectedExport} />
                )}
            </fieldset>
        </form>
    );
}

export default function AccountingExport() {
    return (
        <div>
            <h2>Exportera SIE-fil</h2>
            <p>
                På denna sida kan du exportera transaktioner för vald period
                till en SIE-fil.
            </p>
            <StartExportForm />
            <DownloadExportForm />
        </div>
    );
}
