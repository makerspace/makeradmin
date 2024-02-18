import { render } from "preact";
import { useState } from "preact/hooks";
import * as common from "./common";
import { redirect_to_member_page } from "./login";
declare var UIkit: any;

const ResetPassword = ({ token }: { token: string }) => {
    const [password, setPassword] = useState("");

    return <div id="content">
        <div class="content-centering">
            <h1 style="text-align: center;">Reset password</h1>
            <form
                class="uk-form"
                onSubmit={(e) => {
                    e.preventDefault();

                    common.ajax("POST", window.apiBasePath + "/oauth/password_reset", {
                        reset_token: token,
                        unhashed_password: password,
                    }).then(async (response) => {
                        await UIkit.modal.alert("New password was successfully set!");
                        redirect_to_member_page();
                    }).catch((response: common.ServerResponse<any>) => {
                        UIkit.modal.alert("Failed to set password: " + common.get_error(response));
                    });
                }}
            >

                <div class={"uk-form-row password-field"} style="margin: 16px 0;">
                    <input
                        autoFocus
                        class="uk-form-large uk-width-1-1"
                        type="password"
                        id="password"
                        placeholder="New password"
                        value={password}
                        onChange={(e) =>
                            setPassword(e.currentTarget.value)
                        }
                    />
                </div>
                <div class="uk-form-row" style="margin: 16px 0;">
                    <button
                        type="submit"
                        class="uk-width-1-1 uk-button uk-button-primary uk-button-large"
                    >
                        <span class="uk-icon-check" />
                        Set new password
                    </button>
                </div>
            </form>
        </div>
    </div>
}

common.documentLoaded().then(() => {
    const root = document.querySelector("#root") as HTMLElement;
    var searchParams = new URLSearchParams(window.location.search);
    render(<ResetPassword token={searchParams.get("reset_token") || ""} />, root);
});
