import { render } from "preact";
import { useState } from "preact/hooks";
import * as common from "./common";
import { ServerResponse } from "./common";
import { Sidebar } from "./sidebar";
declare var UIkit: any;

function showSuccess(message: string) {
    UIkit.notification(message, { timeout: 0, status: "success" });
}

function showError(message: string) {
    UIkit.notification(message, { timeout: 0, status: "danger" });
}

export function login_via_password(
    tag: string,
    password: string,
    redirect: string | null,
) {
    const apiBasePath = window.apiBasePath;
    common.removeToken();

    common
        .ajax("POST", apiBasePath + "/oauth/token", {
            grant_type: "password",
            username: tag,
            password,
        })
        .catch((response: ServerResponse<any>) => {
            if (response.status === common.UNAUTHORIZED) {
                return Promise.reject(
                    "Felaktig email/medlemsnummer eller lösenord.",
                );
            }

            return Promise.reject(
                "Oväntad statuskod (" + response.status + ") från servern.",
            );
        })
        .catch((msg) => {
            showError("<h2>Inloggningen misslyckades</h2>" + msg);
            return Promise.reject(null);
        })
        .then((data) => {
            let r = data as ServerResponse<any> & { access_token: string };
            common.login(r.access_token);
            window.location.replace(redirect || "/");
        });
}

export function login_via_single_use_link(
    tag: string,
    redirect: string | null,
) {
    const apiBasePath = window.apiBasePath;
    common.removeToken();

    const data: any = { user_identification: tag };
    if (redirect) {
        data["redirect"] = redirect;
    }

    common
        .ajax("POST", apiBasePath + "/member/send_access_token", data)
        .then((json) => {
            // Yay, success, refresh page
            if (json.data.status === "sent") {
                showSuccess(
                    "Ett mail har skickats till dig med en inloggningslänk, använd den för att logga in.",
                );
            } else {
                showError(
                    "<h2>Inloggningen misslyckades</h2>Tog emot ett oväntat svar från servern:<br><br>" +
                        json.data.status,
                );
            }
        })
        .catch((json) => {
            if (json.status === "not found") {
                showError(
                    "<h2>Inloggningen misslyckades</h2>Hittar inte email eller medlemsnummer.",
                );
            } else {
                showError(
                    "<h2>Inloggningen misslyckades</h2>Tog emot ett oväntat svar från servern:<br><br>" +
                        json.message,
                );
            }
        })
        .catch(() => {
            showError(
                "<h2>Inloggningen misslyckades</h2>Kunde inte kommunicera med servern.",
            );
        });
}

export function render_login(
    root: HTMLElement,
    heading: string | null,
    redirect: string | null,
) {
    render(<LoginPage heading={heading} redirect={redirect} />, root);
}

enum LoginMethod {
    EmailLink = "EmailLink",
    EmailAndPassword = "EmailAndPassword",
}

export const Login = ({ redirect }: { redirect: string | null }) => {
    const [tag, setTag] = useState("");
    const [password, setPassword] = useState("");

    let [loginMethod, setLoginMethod] = useState(
        LoginMethod[
            (localStorage.getItem("last_login_method") ??
                "") as keyof typeof LoginMethod
        ] ?? LoginMethod.EmailLink,
    );

    // Use in case a password manager has filled in the password field, even if it was hidden
    if (password != "") {
        setLoginMethod(LoginMethod.EmailAndPassword);
    }

    return (
        <>
            <form
                class="uk-form"
                onSubmit={(e) => {
                    e.preventDefault();
                    // Error handling
                    if (!tag) {
                        UIkit.modal.alert("Du måste fylla i din E-postadress");
                        return;
                    }

                    if (
                        loginMethod == LoginMethod.EmailAndPassword &&
                        !password
                    ) {
                        UIkit.modal.alert("Du måste fylla i ditt lösenord");
                        return;
                    }

                    localStorage.setItem("last_login_method", loginMethod);

                    if (loginMethod === LoginMethod.EmailLink) {
                        login_via_single_use_link(tag.trim(), redirect);
                    } else {
                        login_via_password(tag.trim(), password, redirect);
                    }
                }}
            >
                <div class="uk-form-row" style="margin: 16px 0;">
                    <input
                        autoFocus
                        class="uk-form-large uk-width-1-1"
                        type="text"
                        id="email"
                        placeholder="Email/Medlemsnummer"
                        value={tag}
                        onChange={(e) => setTag(e.currentTarget.value)}
                        autoComplete="username"
                    />
                </div>

                <div
                    class={
                        "uk-form-row password-field " +
                        (loginMethod === LoginMethod.EmailLink ? "hidden" : "")
                    }
                >
                    <input
                        autoFocus
                        class="uk-form-large uk-width-1-1"
                        type="password"
                        id="password"
                        placeholder="Lösenord"
                        value={password}
                        onChange={(e) => setPassword(e.currentTarget.value)}
                        autoComplete="current-password"
                    />
                </div>

                <div class="uk-form-row" style="margin: 16px 0;">
                    <button
                        type="submit"
                        class="uk-width-1-1 uk-button uk-button-primary uk-button-large"
                    >
                        <span class="uk-icon-check" />
                        Gå vidare
                    </button>
                </div>
            </form>
            <p style="text-align: center;">
                <a
                    role="button"
                    onClick={() => {
                        if (loginMethod === LoginMethod.EmailAndPassword) {
                            // Clear password when switching away from password login
                            setPassword("");
                        }
                        setLoginMethod(
                            loginMethod === LoginMethod.EmailLink
                                ? LoginMethod.EmailAndPassword
                                : LoginMethod.EmailLink,
                        );
                    }}
                >
                    {loginMethod === LoginMethod.EmailLink
                        ? "Logga in med lösenord"
                        : "Logga in med endast email"}
                </a>
            </p>
            <p style="text-align: center;">
                <a href="/shop/register">Bli medlem / Become a member</a>
            </p>
        </>
    );
};

function LoginPage({
    heading,
    redirect,
}: {
    heading: string | null;
    redirect: string | null;
}) {
    heading = heading || "Logga in";

    return (
        <>
            <Sidebar cart={null} />
            <div id="content">
                <div class="content-centering">
                    <div class="uk-width-medium">
                        <h1 style="text-align: center;">{heading}</h1>
                        <Login redirect={redirect} />
                    </div>
                </div>
            </div>
        </>
    );
}

export function redirect_to_member_page() {
    window.location.href = "/member";
}
