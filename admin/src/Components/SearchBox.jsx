import React from "react";

const SearchBox = ({ value, handleChange }) => {
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
                                value={value}
                                tabIndex="1"
                                type="text"
                                className="uk-form-width-large"
                                placeholder="Skriv in ett sökord"
                                onChange={(e) => handleChange(e.target.value)}
                            />
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default SearchBox;
