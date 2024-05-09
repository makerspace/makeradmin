import { render } from "preact";
import * as common from "./common";
import { UNAUTHORIZED } from "./common";
import * as login from "./login";
import { Sidebar } from "./sidebar";
declare var UIkit: any;

const LicensesPage = () => {
    return (
        <>
            <Sidebar cart={null} />
            <div id="content">
                <div className="content-centering">{licenses_content}</div>
            </div>
        </>
    );
};

const apiBasePath = window.apiBasePath;
const future1 = common.ajax("GET", apiBasePath + "/member/current", null);

common.documentLoaded().then(() => {
    const root = document.querySelector("#root") as HTMLElement;

    future1
        .then((member_json) => {
            root.innerHTML = "";
            render(<LicensesPage />, root);
        })
        .catch((e) => {
            // Probably Unauthorized, redirect to login page.
            if (e.status === UNAUTHORIZED) {
                // Render login
                login.render_login(root, null, null);
            } else {
                UIkit.modal.alert("<h2>Failed to load member info</h2>");
            }
        });
});
