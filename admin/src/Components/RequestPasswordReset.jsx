import React from "react";
import auth from "../auth";
import { withRouter } from "react-router";
import { browserHistory } from "../browser_history";
import { showError, showSuccess } from "../message";

class RequestPasswordReset extends React.Component {
    cancel() {
        browserHistory.push("/");
    }

    submit(e) {
        e.preventDefault();

        const user_identification = this.user_identification.value;

        // Error handling
        if (!user_identification) {
            showError("You need to fill your email or member number.");
            return;
        }

        auth.requestPasswordReset(user_identification).then(() => {
            showSuccess(
                "Link to password reset will be sent to your email shortly.",
            );
            browserHistory.push("/");
        });
    }

    render() {
        return (
            <div className="uk-vertical-align uk-text-center uk-height-1-1">
                <div
                    className="uk-vertical-align-middle"
                    style={{ width: "300px" }}
                >
                    <div className="uk-text-left">
                        <form
                            className="uk-panel uk-panel-box uk-form"
                            onSubmit={this.submit.bind(this)}
                        >
                            <div className="uk-form-row">
                                <h2>Glömt ditt lösenord?</h2>
                            </div>

                            <div className="uk-form-row">
                                <p>
                                    Fyll i ditt användarnamn så skickar vi
                                    instruktioner om hur du nollställer ditt
                                    lösenord.
                                </p>
                            </div>

                            <div className="uk-form-row">
                                <div className="uk-form-icon">
                                    <i className="uk-icon-user" />
                                    <input
                                        ref={(c) => {
                                            this.user_identification = c;
                                        }}
                                        className="uk-form-large uk-form-width-large"
                                        type="text"
                                        placeholder="Användarnamn"
                                    />
                                </div>
                            </div>

                            <div className="uk-form-row">
                                <button
                                    type="submit"
                                    className="uk-width-1-1 uk-button uk-button-success uk-button-large"
                                >
                                    <span className="uk-icon-check" /> Skicka
                                    epost
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }
}

export default withRouter(RequestPasswordReset);
