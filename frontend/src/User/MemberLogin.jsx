import React from 'react';
import auth from '../auth';


export default class MemberLogin extends React.Component {

    onSubmit(e) {
        e.preventDefault();
        const tag = this.refs.tag.value;

        // Error handling
        if (!tag) {
            UIkit.modal.alert("Du måste fylla i din E-postadress");
            return;
        }
        auth.login_via_single_use_link(tag);
    }

    render() {
        return (
            <div className="uk-vertical-align uk-text-center uk-height-1-1">
                <div className="uk-vertical-align-middle" style={{width: "300px"}}>
                    <div className="uk-text-left">
                        <form className="uk-panel uk-panel-box uk-form" onSubmit={e => this.onSubmit(e)}>
                            <div className="uk-form-row">
                                <h2>Logga in</h2>
                            </div>
                            
                            <div className="uk-form-row">
                                <div className="uk-form-icon">
                                    <i className="uk-icon-user"/>
                                    <input autoFocus ref="tag" className="uk-form-large uk-form-width-large" type="text" placeholder="Email/Medlemsnummer"/>
                                </div>
                            </div>
                            
                            <div className="uk-form-row">
                                <button className="uk-width-1-1 uk-button uk-button-primary uk-button-large"><span
                                    className="uk-icon-check"/> Gå vidare
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        );
     }
}