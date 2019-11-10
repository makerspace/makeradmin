import React from 'react';
import auth from '../auth';
import { withRouter } from 'react-router';
import {showError, showSuccess} from "../message";

class PasswordReset extends React.Component {
    
    submit(e) {
        e.preventDefault();
        console.log("sub");
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
                                    <input ref={c => { this.password = c; }} className="uk-form-large uk-form-width-large" type="password" placeholder="New Password" />
                                </div>
                            </div>

                            <div className="uk-form-row">
                                <button type="submit" className="uk-width-1-1 uk-button uk-button-success uk-button-large"><span className="uk-icon-check" /> Submit</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
    }
}


export default withRouter(PasswordReset);
