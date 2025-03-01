import { render } from "preact";
import { useState } from "preact/hooks";
import * as common from "./common";
import { ServerResponse } from "./common";
import { Translator, useTranslation } from "./i18n";
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
    t: Translator<"login">,
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
                return Promise.reject(t("errors.bad_credentials"));
            }

            return Promise.reject(
                t("errors.generic", { error: response.status }),
            );
        })
        .catch((msg) => {
            showError(`<h2>${t("errors.title_failed")}</h2> ${msg}`);
            return null;
        })
        .then((data) => {
            if (data !== null) {
                let r = data as ServerResponse<any> & { access_token: string };
                common.login(r.access_token);
                window.location.replace(redirect || "/");
            }
        });
}

export function login_via_single_use_link(
    tag: string,
    redirect: string | null,
    t: Translator<"login">,
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
                showSuccess(t("magic_link_sent"));
            } else {
                showError(
                    `<h2>${t("errors.title_failed")}</h2>${t("errors.generic", {
                        error: json.data.status,
                    })}`,
                );
            }
        })
        .catch((json) => {
            if (json.status === "not found") {
                showError(
                    `<h2>${t("errors.title_failed")}</h2>${t(
                        "errors.no_such_user",
                    )}`,
                );
            } else {
                showError(
                    `<h2>${t("errors.title_failed")}</h2>${t("errors.generic", {
                        error: json.message,
                    })}`,
                );
            }
        })
        .catch(() => {
            showError(
                `<h2>${t("errors.title_failed")}</h2>${t("errors.generic2")}`,
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
    const { t } = useTranslation("login");

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
                        UIkit.modal.alert(t("form_validation.missing_tag"));
                        return;
                    }

                    if (
                        loginMethod == LoginMethod.EmailAndPassword &&
                        !password
                    ) {
                        UIkit.modal.alert(
                            t("form_validation.missing_password"),
                        );
                        return;
                    }

                    localStorage.setItem("last_login_method", loginMethod);

                    if (loginMethod === LoginMethod.EmailLink) {
                        login_via_single_use_link(tag.trim(), redirect, t);
                    } else {
                        login_via_password(tag.trim(), password, redirect, t);
                    }
                }}
            >
                <div class="uk-form-row" style="margin: 16px 0;">
                    <input
                        autoFocus
                        class="uk-form-large uk-width-1-1"
                        type="text"
                        id="email"
                        placeholder={t("tag_placeholder")}
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
                        placeholder={t("password_placeholder")}
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
                        {t("continue")}
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
                        ? t("login_methods.email_and_password")
                        : t("login_methods.email_link")}
                </a>
            </p>
            <p style="text-align: center;">
                <a href="/shop/register">{t("register")}</a>
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
    const { t } = useTranslation("login");
    heading = heading || t("title");

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
