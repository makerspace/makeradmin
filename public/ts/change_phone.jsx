import * as common from "./common"
import * as login from "./login"
import { UNAUTHORIZED } from "./common";
import {Component, render} from "preact";

class ChangePhone extends Component {
    
    constructor(props) {
        super(props);
        this.state = {
            state: "intro",
            submitInProgress: false,
        }
    }
    
    render() {
        return (
            <div>
                <form className="uk-form uk-form-stacked uk-margin-bottom" xmlns="http://www.w3.org/1999/html"
                      onSubmit={e => {
                          e.preventDefault();
                          UIkit.modal.alert("You need to enter your email");
                      }}
                >
                    <h1 style="text-align: center;">Nytt telefonnummer</h1>
                    <div className="uk-form-row" style="margin: 16px 0;">
                        <input autoFocus ref="tag" className="uk-form-large uk-width-1-1" type="tel"
                               placeholder="Telefonnummer"/>
                    </div>
                    
                    <div className="uk-form-row" style="margin: 16px 0;">
                        <button className="uk-width-1-1 uk-button uk-button-primary uk-button-large"><span
                            className="uk-icon-check"/>Skicka valideringskod
                        </button>
                    </div>
                </form>
                <form className="uk-form uk-form-stacked uk-margin-bottom" xmlns="http://www.w3.org/1999/html">
                    <h1 style="text-align: center;">Validera telefonnummer</h1>
                    <div className="uk-form-row" style="margin: 16px 0;">
                        <input autoFocus ref="tag" className="uk-form-large uk-width-1-1" type="number"
                               placeholder="Valideringkod"/>
                    </div>
                    
                    <div className="uk-form-row" style="margin: 16px 0;">
                        <button className="uk-width-1-1 uk-button uk-button-primary uk-button-large"><span
                            className="uk-icon-check"/>Validera
                        </button>
                    </div>
                </form>
            </div>
        );
    }
}

common.documentLoaded().then(() => {
    common.addSidebarListeners();
    const content = document.getElementById("content")
    const apiBasePath = window.apiBasePath;
    render(<ChangePhone/>, content);
});
