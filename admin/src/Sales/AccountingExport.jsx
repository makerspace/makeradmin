import React from 'react';
import Select from "react-select";
import auth from "../auth";

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

    exportAccounting() {
        this.setState({ state: "loading" });
        let file_name = "accounting_created_file_1.txt";

        // auth.save_accounting_data(file_name);
        // auth.export_accounting_file(file_name);
        // fetch("/post_file/" + filename_upload, {
        //     method: "POST",
        //     body: "hej på dig!", // file data
        //     // headers: { 'Content-Type': 'application/json; charset=UTF-8' },
        // });


        // fetch("/uploads/" + filename_download);

        // TODO: to the export of SIE file

        this.setState({ state: "loaded" });

        // this.state.selectedOption_from;
        // this.state.selectedOption_to;
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
                    <p>På denna sida kan du exportera transaktioner för vald period till en SIE-fil.</p>

                    <form className="uk-form uk-form-stacked">
                        <fieldset className="uk-margin-top">
                            <legend><i className="uk-icon-shopping-cart" /> Välj vilken period du vill exportera</legend>
                            <label className="uk-form-label" htmlFor="">
                                Från och med år:
                            </label>
                            <Select name="from_year"
                                className="uk-select"
                                tabIndex={1}
                                options={years}
                                value={selectedOption_from}
                                getOptionValue={g => g.year}
                                getOptionLabel={g => g.year}
                                onChange={from_year => this.selectOptionFrom(from_year)}
                            />
                            <label className="uk-form-label" htmlFor="">
                                Till och med år:
                            </label>
                            <Select name="to_year"
                                className="uk-select"
                                tabIndex={1}
                                options={years}
                                value={selectedOption_to}
                                getOptionValue={g => g.year}
                                getOptionLabel={g => g.year}
                                onChange={to_year => this.selectOptionTo(to_year)}
                            />

                            <div className="uk-button uk-button-primary" role="button" style={{ marginTop: "2px" }} onClick={() => this.exportAccounting()}>
                                Exportera SIE-fil för vald period{this.state.state === "loading" ? "..." : ""}
                                {/* {this.state.csv_content && (
                                    <textarea
                                        readOnly
                                        className="uk-width-1-1"
                                        value={this.state.csv_content}
                                        rows={50}
                                    ></textarea>
                                )} */}
                                {/* {!this.state.csv_content && (
                                    <a className="uk-button uk-button-primary" role="button" style={{ marginTop: "2px" }} onClick={() => this.exportAccounting()}>
                                        Exportera SIE-fil för vald period{this.state.state === "loading" ? "..." : ""}
                                    </a>
                                )} */}
                            </div>
                        </fieldset>
                    </form>
                </div>
            </div>
        );
    }
}

export default AccountingExport;

