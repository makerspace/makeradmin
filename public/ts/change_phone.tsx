import * as common from "./common"
import * as login from "./login"
import { UNAUTHORIZED } from "./common";
import {Component, render} from "preact";

declare var UIkit: any;

interface State {
    requestSubmitInProgress: boolean,
    requestSent: boolean,
    validateSubmitInProgress: boolean,
}

interface Props {
    id: number
}

class ChangePhone extends Component<Props, State> {
    
    constructor(props: any) {
        super(props);
        this.state = {
            requestSubmitInProgress: false,
            requestSent: false,
            validateSubmitInProgress: false,
        }
    }
    
    async submitPhoneNumber(number: string) {
        try {
            this.setState({requestSubmitInProgress: true})
            await common.ajax("POST", `${window.apiBasePath}/member/current/change_phone_request`, {phone: number.trim()});
            this.setState({requestSent: true})
        } catch (error) {
            UIkit.modal.alert("<h2>" + error.status + "</h2><p>" + error.message + "</p>");
        }
        this.setState({requestSent: true,})
        // UIkit.modal.alert("You need to enter your email" + number.trim());
        //common.ajax("POST", `${window.apiBasePath}/member/current/change_phone_validate`, {code: number.trim()});
    }
    
    render() {
        const {requestSubmitInProgress} = this.state;
        
        return <>
                <form className="uk-form uk-form-stacked uk-margin-bottom"
                      onSubmit={e => {
                          e.preventDefault();
                          const input = document.getElementById('phone') as HTMLInputElement;
                          if (input != null) {
                              this.submitPhoneNumber(input.value);
                          }
                  }}
                >
                    <h1 style="text-align: center;">Nytt telefonnummer</h1>
                    <div className="uk-form-row" style="margin: 16px 0;">
                        <input id="phone" tabIndex={1} autoFocus className="uk-form-large uk-width-1-1" type="tel"  placeholder="Telefonnummer"/>
                    </div>
                    <div className="uk-form-row" style="margin: 16px 0;">
                        <button className="uk-width-1-1 uk-button uk-button-primary uk-button-large" disabled={requestSubmitInProgress}><span className="uk-icon-check"/>Skicka valideringskod</button>
                    </div>
                </form>
                <form className="uk-form uk-form-stacked uk-margin-bottom">
                    <h1 style="text-align: center;">Validera telefonnummer</h1>
                    <div className="uk-form-row" style="margin: 16px 0;">
                        <input id="code" tabIndex={2} autoFocus className="uk-form-large uk-width-1-1" type="number" placeholder="Valideringkod"/>
                    </div>
                    
                    <div className="uk-form-row" style="margin: 16px 0;">
                        <button className="uk-width-1-1 uk-button uk-button-primary uk-button-large"><span className="uk-icon-check"/>Validera</button>
                    </div>
                </form>
        </>;
    }
}


common.documentLoaded().then(() => {
    common.addSidebarListeners();
    
    const content = document.getElementById("content")
    if (content != null) {
        render(<ChangePhone id={1}/>, content);
    }
});
