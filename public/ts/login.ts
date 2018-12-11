import * as common from "./common"
declare var UIkit: any;

function showSuccess(message: string) {
	UIkit.notification(message, {timeout: 0, status: "success"});
}

function showError(message: string) {
    UIkit.notification(message, {timeout: 0, status: "danger"});
}

function login_via_single_use_link(tag: string) {
	const apiBasePath = window.apiBasePath;

    common.ajax("POST", apiBasePath + "/member/send_access_token",
            {
            	user_tag: tag
            }
    ).then(json => {
    	// Yay, success, refresh page
    	if (json.status === "sent") {
            showSuccess("Ett mail har skickats till dig med en inloggningslänk, använd den för att logga in.");
        } else {
            showError("<h2>Inloggningen misslyckades</h2>Tog emot ett oväntat svar från servern:<br><br>" + json.status);
        }
    })
    .catch(json => {
            if (json.status === "ambiguous") {
                showError("<h2>Inloggningen misslyckades</h2>Det finns flera medlemmar som matchar '" + tag + "'. Välj något som är mer unikt, t.ex email eller medlemsnummer.");
            }
            else if (json.status === "not found") {
                showError("<h2>Inloggningen misslyckades</h2>Ingen medlem med det namnet, email eller medlemsnummer existerar.");
            }
            else {
                showError("<h2>Inloggningen misslyckades</h2>Tog emot ett oväntat svar från servern:<br><br>" + json.status);
            }
        })
        .catch(() => {
            showError("<h2>Inloggningen misslyckades</h2>Kunde inte kommunicera med servern.");
        }
    );
}

export function logout() {
	localStorage.setItem("token", null);
	// TODO: Correct URL?
	window.location.href = "/";
}

export function render_login(root: HTMLElement, heading: string) {
    heading = heading || "Logga in";
	root.innerHTML = `<form className="uk-panel uk-panel-box uk-form">
            <div className="uk-form-row">
                <h1>${heading}</h1>
            </div>
            
            <div className="uk-form-row">
                <div className="uk-form-icon">
                    <i className="uk-icon-user"/>
                    <input autoFocus ref="tag" className="uk-form-large uk-form-width-large" type="text" placeholder="Email/Medlemsnummer"/>
                </div>
            </div>
            
            <div className="uk-form-row">
                <button className="uk-width-1-1 uk-button uk-button-primary uk-button-large"><span className="uk-icon-check"/>
                	Gå vidare
                </button>
            </div>
        </form>`;
	const element = <HTMLElement>root.firstChild;
	console.log(element);
	const tagInput = <HTMLInputElement>element.getElementsByTagName("input")[0];
	element.onsubmit = e => {
		e.preventDefault();
        const tag = tagInput.value;

        // Error handling
        if (!tag) {
            UIkit.modal.alert("Du måste fylla i din E-postadress");
            return;
        }

        login_via_single_use_link(tag);
	}
}
