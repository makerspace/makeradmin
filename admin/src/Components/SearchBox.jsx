import React from "react";

export default class SearchBox extends React.Component {
    render() {
        return (
            <div className="filterbox">
                <div className="uk-grid">
                    <div className="uk-width-2-3">
                        <form
                            className="uk-form"
                            onSubmit={(e) => e.preventDefault()}
                        >
                            <div className="uk-form-icon">
                                <i className="uk-icon-search" />
                                <input
                                    value={this.props.value}
                                    ref={(c) => (this.search = c)}
                                    tabIndex="1"
                                    type="text"
                                    className="uk-form-width-large"
                                    placeholder="Skriv in ett sökord"
                                    onChange={(e) =>
                                        this.props.handleChange(e.target.value)
                                    }
                                />
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }
}
