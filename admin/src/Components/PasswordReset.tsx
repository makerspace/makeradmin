import auth from "../auth";
import { browserHistory } from "../browser_history";
import { showError, showSuccess } from "../message";
import { Link } from "react-router-dom";
import { withRouter } from "react-router";
import React from "react";
import * as _ from "underscore";
class PasswordReset extends React.Component {
    input = React.createRef<HTMLInputElement>();

    constructor(props: any) {
        super(props);
    }

    submit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        const password = this.input.current.value;
        const token = new RegExp("^\\?reset_token=([^&]*)$").exec(
            browserHistory.location.search,
        )[1];

        auth.passwordReset(token, password).then((response) => {
            const error_message = response.data.error_message;
            if (_.isEmpty(error_message)) {
                showSuccess("New password was successfully set!");
                browserHistory.push("/");
            } else {
                showError(error_message);
            }
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
                            onSubmit={(e) => this.submit(e)}
                        >
                            <div className="uk-form-row">
                                <h2>Password Reset</h2>
                            </div>
                            <div className="uk-form-row">
                                <div className="uk-form-icon">
                                    <i className="uk-icon-user" />
                                    <input
                                        ref={this.input}
                                        className="uk-form-large uk-form-width-large"
                                        type="password"
                                        placeholder="New Password"
                                    />
                                </div>
                            </div>

                            <div className="uk-form-row">
                                <button
                                    type="submit"
                                    className="uk-width-1-1 uk-button uk-button-success uk-button-large"
                                >
                                    <span className="uk-icon-check" /> Submit
                                </button>
                            </div>
                            <div className="uk-form-row uk-text-small">
                                <Link
                                    className="uk-link uk-link-muted"
                                    to="/request-password-reset"
                                >
                                    Request another passsword reset.
                                </Link>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }
}

export default withRouter(PasswordReset);
