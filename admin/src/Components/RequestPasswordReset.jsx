import React, { useState } from "react";
import { withRouter } from "react-router";
import auth from "../auth";
import { browserHistory } from "../browser_history";
import { showError, showSuccess } from "../message";

const RequestPasswordReset = () => {
    const [userIdentification, setUserIdentification] = useState("");

    const handleInputChange = (e) => {
        setUserIdentification(e.target.value);
    };

    const submit = (e) => {
        e.preventDefault();

        if (!userIdentification) {
            showError("You need to fill your email or member number.");
            return;
        }

        auth.requestPasswordReset(userIdentification).then(() => {
            showSuccess(
                "Link to password reset will be sent to your email shortly.",
            );
            browserHistory.push("/");
        });
    };

    return (
        <div className="uk-vertical-align uk-text-center uk-height-1-1">
            <div
                className="uk-vertical-align-middle"
                style={{ width: "300px" }}
            >
                <div className="uk-text-left">
                    <form
                        className="uk-panel uk-panel-box uk-form"
                        onSubmit={submit}
                    >
                        <div className="uk-form-row">
                            <h2>Glömt ditt lösenord?</h2>
                        </div>

                        <div className="uk-form-row">
                            <p>
                                Fyll i ditt email eller medlemsnummer så skickar
                                vi instruktioner om hur du nollställer ditt
                                lösenord.
                            </p>
                        </div>

                        <div className="uk-form-row">
                            <div className="uk-form-icon">
                                <i className="uk-icon-user" />
                                <input
                                    value={userIdentification}
                                    onChange={handleInputChange}
                                    className="uk-form-large uk-form-width-large"
                                    type="text"
                                    placeholder="Email/Medlemsnummer"
                                    autoComplete="username"
                                />
                            </div>
                        </div>

                        <div className="uk-form-row">
                            <button
                                type="submit"
                                className="uk-width-1-1 uk-button uk-button-success uk-button-large"
                            >
                                <span className="uk-icon-check" /> Skicka epost
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default withRouter(RequestPasswordReset);
