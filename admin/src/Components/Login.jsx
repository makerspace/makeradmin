import React, { useRef } from "react";
import { Link } from "react-router-dom";
import auth from "../auth";
import { showError } from "../message";

const Login = () => {
    const usernameRef = useRef(null);
    const passwordRef = useRef(null);

    const login = (e) => {
        e.preventDefault();
        const username = usernameRef.current.value;
        const password = passwordRef.current.value;

        if (!username || !password) {
            showError("Du måste fylla i email/medlemsnummer och lösenord");
            return;
        }

        auth.login(username, password);
    };

    return (
        <div className="uk-vertical-align uk-text-center uk-height-1-1">
            <div
                className="uk-vertical-align-middle"
                style={{ width: "300px" }}
            >
                <form
                    className="uk-panel uk-panel-box uk-form"
                    onSubmit={login}
                >
                    <div className="uk-form-row">
                        <h2>Logga in</h2>
                    </div>

                    <div className="uk-form-row">
                        <div className="uk-form-icon">
                            <i className="uk-icon-user" />
                            <input
                                ref={usernameRef}
                                className="uk-form-large uk-form-width-large"
                                type="text"
                                placeholder="Email/Medlemsnummer"
                                autoComplete="username"
                            />
                        </div>
                    </div>

                    <div className="uk-form-row">
                        <div className="uk-form-icon">
                            <i className="uk-icon-lock" />
                            <input
                                ref={passwordRef}
                                className="uk-form-large uk-form-width-large"
                                type="password"
                                placeholder="Lösenord"
                                autoComplete="current-password"
                            />
                        </div>
                    </div>

                    <div className="uk-form-row">
                        <button
                            type="submit"
                            className="uk-width-1-1 uk-button uk-button-primary uk-button-large"
                        >
                            Logga in
                        </button>
                    </div>

                    <div className="uk-form-row uk-text-small">
                        <Link
                            className="uk-float-right uk-link uk-link-muted"
                            to="/request-password-reset"
                        >
                            Glömt ditt lösenord?
                        </Link>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default Login;
