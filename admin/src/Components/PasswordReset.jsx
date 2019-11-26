import React from 'react';
import auth from '../auth';
import { withRouter } from 'react-router';
import {showError, showSuccess} from "../message";
import { Link } from 'react-router';
import * as _ from "underscore";

class PasswordReset extends React.Component {
    
    constructor(props) {
        super(props);
        this.input = {};
    }
    
    submit(e) {
        e.preventDefault();
        const password = this.input.value;
        const token = this.props.location.query.reset_token;
        
        auth.passwordReset(token, password)
            .then(response => {
                const error_message = response.data.error_message;
                if (_.isEmpty(error_message)) {
                    showSuccess("New password was successfully set!");
                    this.props.router.push("/");
                }
                else {
                    showError(error_message);
                }
            })
        ;
    }
    
    render() {
        return (
            <div className="uk-vertical-align uk-text-center uk-height-1-1">
                <div className="uk-vertical-align-middle" style={{width: "300px"}}>
                    <div className="uk-text-left">
                        <form className="uk-panel uk-panel-box uk-form" onSubmit={e => this.submit(e)}>
                            <div className="uk-form-row">
                                <h2>Password Reset</h2>
                            </div>
                            <div className="uk-form-row">
                                <div className="uk-form-icon">
                                    <i className="uk-icon-user"/>
                                    <input ref={i => { this.input = i; }} className="uk-form-large uk-form-width-large" type="password" placeholder="New Password" />
                                </div>
                            </div>

                            <div className="uk-form-row">
                                <button type="submit" className="uk-width-1-1 uk-button uk-button-success uk-button-large"><span className="uk-icon-check" /> Submit</button>
                            </div>
                            <div className="uk-form-row uk-text-small">
                                <Link className="uk-link uk-link-muted" to="/request-password-reset">Request another passsword reset.</Link>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }
}


export default withRouter(PasswordReset);
