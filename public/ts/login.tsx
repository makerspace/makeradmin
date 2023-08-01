import { useState } from "preact/hooks";
import * as common from "./common"
import { Sidebar } from "./sidebar";
import { render } from "preact";
declare var UIkit: any;

function showSuccess(message: string) {
    UIkit.notification(message, { timeout: 0, status: "success" });
}

function showError(message: string) {
    UIkit.notification(message, { timeout: 0, status: "danger" });
}

export function login_via_single_use_link(tag: string, redirect: string | null) {
    const apiBasePath = window.apiBasePath;
    common.removeToken();

    const data: any = { user_identification: tag };
    if (redirect) {
        data['redirect'] = redirect;
    }

    common.ajax("POST", apiBasePath + "/member/send_access_token", data)
        .then(json => {
            // Yay, success, refresh page
            if (json.data.status === "sent") {
                showSuccess("Ett mail har skickats till dig med en inloggningslänk, använd den för att logga in.");
            } else {
                showError("<h2>Inloggningen misslyckades</h2>Tog emot ett oväntat svar från servern:<br><br>" + json.data.status);
            }
        })
        .catch(json => {
            if (json.status === "not found") {
                showError("<h2>Inloggningen misslyckades</h2>Hittar inte email eller medlemsnummer.");
            } else {
                showError("<h2>Inloggningen misslyckades</h2>Tog emot ett oväntat svar från servern:<br><br>" + json.message);
            }
        })
        .catch(() => {
            showError("<h2>Inloggningen misslyckades</h2>Kunde inte kommunicera med servern.");
        }
        );
}

export function render_login(root: HTMLElement, heading: string | null, redirect: string | null) {
    render(<Login heading={heading} redirect={redirect} />, root);
}

function Login({ heading, redirect }: { heading: string | null, redirect: string | null }) {
    heading = heading || "Logga in";
    const [tag, setTag] = useState("");
    return <>
        <Sidebar cart={null} />
        <div id="content">
            <div class="content-centering">
                <div class="uk-width-medium">
                    <h1 style="text-align: center;">{heading}</h1>
                    <form class="uk-form" onSubmit={e => {
                        e.preventDefault();
                        // Error handling
                        if (!tag) {
                            UIkit.modal.alert("Du måste fylla i din E-postadress");
                            return;
                        }

                        login_via_single_use_link(tag.trim(), redirect);
                    }}>
                        <div class="uk-form-row" style="margin: 16px 0;">
                            <input autoFocus class="uk-form-large uk-width-1-1" type="text" placeholder="Email/Medlemsnummer" value={tag} onChange={e => setTag(e.currentTarget.value)} />
                        </div>

                        <div class="uk-form-row" style="margin: 16px 0;">
                            <button type="submit" class="uk-width-1-1 uk-button uk-button-primary uk-button-large"><span class="uk-icon-check" />
                                Gå vidare
                            </button>
                        </div>
                    </form>
                    <p style="text-align: center;"><a href="/shop/register">Bli medlem / Become a member</a></p>
                </div>
            </div>
        </div>
    </>
}

export function redirect_to_member_page() {
    window.location.href = "/member";
}
