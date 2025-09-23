import React from "react";
import { Link } from "react-router-dom";
import * as _ from "underscore";
import auth from "../auth";
import { showError, showSuccess } from "../message";
import Icon from "./icons";

class PasswordReset extends React.Component {
    input = React.createRef<HTMLInputElement>();

    submit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        const password = this.input.current!.value;
        const tokens = new RegExp("^\\?reset_token=([^&]*)$").exec(
            window.location.search,
        );
        const token = tokens ? tokens[1] : "";

        auth.passwordReset(token, password).then((response) => {
            const error_message = response.data.error_message;
            if (_.isEmpty(error_message)) {
                showSuccess("New password was successfully set!");
                window.location.href = "/";
            } else {
                showError(error_message);
            }
        });
    }

    override render() {
        return (
            <div className="uk-vertical-align uk-text-center uk-height-1-1">
                <div
                    className="uk-vertical-align-middle"
                    style={{ width: "300px" }}
                >
                    <div className="uk-text-left">
                        <form
                            className="uk-card uk-card-default"
                            onSubmit={(e) => this.submit(e)}
                        >
                            <div className="form-row">
                                <h2>Password Reset</h2>
                            </div>
                            <div className="form-row">
                                <div className="uk-inline">
                                    <Icon form icon="user" />
                                    <input
                                        ref={this.input}
                                        className="uk-form-large uk-form-width-large"
                                        type="password"
                                        placeholder="New Password"
                                        autoComplete="new-password"
                                    />
                                </div>
                            </div>

                            <div className="form-row">
                                <button
                                    type="submit"
                                    className="uk-width-1-1 uk-button uk-button-primary uk-button-large"
                                >
                                    <Icon icon="check" /> Submit
                                </button>
                            </div>
                            <div className="form-row uk-text-small">
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

export default PasswordReset;
