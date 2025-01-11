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
            <div className="form-row">
                <h2>Glömt ditt lösenord?</h2>
            </div>

            <div className="form-row">
                <p>
                    Fyll i ditt email eller medlemsnummer så skickar vi
                    instruktioner om hur du nollställer ditt lösenord.
                </p>
            </div>

            <div className="form-row">
                <div className="uk-inline">
                    <Icon form icon="user" />
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

            <div className="form-row">
                <button
                    type="submit"
                    className="uk-width-1-1 uk-button uk-button-primary uk-button-large"
                >
                    <Icon icon="check" /> Skicka epost
                </button>
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
