import React, { useState } from "react";
import auth from "../auth";
import { browserHistory } from "../browser_history";
import { showError, showSuccess } from "../message";
import { CenteredForm } from "./CenteredForm";
import Icon from "./icons";

const ResetPasswordForm = () => {
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
        <form className="uk-card uk-card-default" onSubmit={submit}>
            <div className="uk-card-header">
                <h2>Glömt ditt lösenord?</h2>
            </div>

            <div className="uk-card-body">
                <div>
                    Fyll i ditt email eller medlemsnummer så skickar vi
                    instruktioner om hur du nollställer ditt lösenord.
                </div>

                <div className="uk-margin-top">
                    <div className="uk-inline uk-width-1-1">
                        <Icon form icon="user" />
                        <input
                            value={userIdentification}
                            onChange={handleInputChange}
                            className="uk-input"
                            type="text"
                            placeholder="Email/Medlemsnummer"
                            autoComplete="username"
                        />
                    </div>
                </div>

                <div className="uk-margin-top">
                    <button
                        type="submit"
                        className="uk-width-1-1 uk-button uk-button-primary uk-button-large"
                    >
                        <Icon icon="check" /> Skicka epost
                    </button>
                </div>
            </div>
        </form>
    );
};

const RequestPasswordReset = () => {
    return (
        <CenteredForm>
            <ResetPasswordForm />
        </CenteredForm>
    );
};

export default RequestPasswordReset;
