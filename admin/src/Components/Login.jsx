import React, { useState } from "react";
import { Link } from "react-router-dom";
import auth from "../auth";
import { showError } from "../message";
import { CenteredForm } from "./CenteredForm";
import Icon from "./icons";

function LoginForm() {
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
        <form className="uk-card uk-card-default uk-card-body" onSubmit={login}>
            <div className="uk-card-header">
                <h2>Logga in</h2>
            </div>

            <div className="uk-card-body">
                <div className="uk-margin-top">
                    <div className="uk-inline uk-width-1-1">
                        <Icon form icon="user" />
                        <input
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="uk-input"
                            type="text"
                            placeholder="Email/Medlemsnummer"
                            autoComplete="username"
                        />
                    </div>
                </div>

                <div className="uk-margin-top">
                    <div className="uk-inline uk-width-1-1">
                        <Icon form icon="lock" />
                        <input
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="uk-input"
                            type="password"
                            placeholder="Lösenord"
                            autoComplete="current-password"
                        />
                    </div>
                </div>

                <div className="uk-margin-top">
                    <button
                        type="submit"
                        className="uk-width-1-1 uk-button uk-button-primary uk-button-large"
                    >
                        Logga in
                    </button>
                </div>

                <div className="uk-margin-top">
                    <Link
                        className="uk-float-right uk-button uk-button-text"
                        to="/request-password-reset"
                    >
                        Glömt ditt lösenord?
                    </Link>
                </div>
            </div>
        </form>
    );
}

const Login = () => {
    return (
        <CenteredForm>
            <LoginForm />
        </CenteredForm>
    );
};

export default Login;
