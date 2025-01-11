import React from "react";
import Icon from "./icons";

const SearchBox = ({ value, handleChange }) => {
    return (
        <form className="searchbox" onSubmit={(e) => e.preventDefault()}>
            <div className="uk-inline uk-width-1-1">
                <Icon form icon="search" />
                <input
                    value={value}
                    tabIndex="1"
                    type="text"
                    className="uk-input"
                    placeholder="Skriv in ett sökord"
                    onChange={(e) => handleChange(e.target.value)}
                />
            </div>
        </form>
    );
};

export default SearchBox;
