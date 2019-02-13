import React from 'react';
import auth from '../auth';
import { withRouter } from 'react-router';
import {showError, showSuccess} from "../message";


class LoginResetPassword extends React.Component {
    
    cancel() {
        this.props.router.push("/");
    }

    submit(e) {
        e.preventDefault();

        let username = this.refs.username.value;

        // Error handling
        if(!username)
        {
            showError("Du måste fylla i din E-postadress");
            return;
        }

        auth.requestPassword(username);

        showSuccess("Ett E-postmeddelande med information om hur du nollställer ditt lösenord har skickats till " + username);
        this.props.router.push("/");
    }

    render() {
        return (
            <div className="uk-vertical-align uk-text-center uk-height-1-1">
                <div className="uk-vertical-align-middle" style={{width: "300px"}}>
                    <div className="uk-text-left">
                        <form className="uk-panel uk-panel-box uk-form" onSubmit={this.submit.bind(this)}>
                            <div className="uk-form-row">
                                <h2>Glömt ditt lösenord?</h2>
                            </div>

                            <div className="uk-form-row">
                                <p>Fyll i ditt användarnamn så skickar vi instruktioner om hur du nollställer ditt lösenord.</p>
                            </div>

                            <div className="uk-form-row">
                                <div className="uk-form-icon">
                                    <i className="uk-icon-user"/>
                                    <input ref="username" className="uk-form-large uk-form-width-large" type="text" placeholder="Användarnamn" />
                                </div>
                            </div>

                            <div className="uk-form-row">
                                <button type="submit" className="uk-width-1-1 uk-button uk-button-success uk-button-large"><span className="uk-icon-check" /> Skicka E-post</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }
}


export default withRouter(LoginResetPassword);