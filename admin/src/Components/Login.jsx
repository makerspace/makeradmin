import React, { useState } from "react";
import { Link } from "react-router-dom";
import auth from "../auth";
import { showError } from "../message";
import Icon from "./icons";

const Login = () => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    const login = (e) => {
        e.preventDefault();

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
                <form className="uk-panel uk-panel-box" onSubmit={login}>
                    <div className="form-row">
                        <h2>Logga in</h2>
                    </div>

                    <div className="form-row">
                        <div className="uk-inline">
                            <Icon form icon="user" />
                            <input
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="uk-form-large uk-form-width-large"
                                type="text"
                                placeholder="Email/Medlemsnummer"
                                autoComplete="username"
                            />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="uk-inline">
                            <Icon form icon="lock" />
                            <input
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="uk-form-large uk-form-width-large"
                                type="password"
                                placeholder="Lösenord"
                                autoComplete="current-password"
                            />
                        </div>
                    </div>

                    <div className="form-row">
                        <button
                            type="submit"
                            className="uk-width-1-1 uk-button uk-button-primary uk-button-large"
                        >
                            Logga in
                        </button>
                    </div>

                    <div className="form-row uk-text-small">
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
