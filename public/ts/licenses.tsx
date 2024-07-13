import { render } from "preact";
import { render as jsx_to_string } from "preact-render-to-string";
import * as common from "./common";
import { UNAUTHORIZED } from "./common";
import * as login from "./login";
import { Sidebar } from "./sidebar";
declare var UIkit: any;

const LicensesPage = ({ licenses_content }: { licenses_content: string }) => {
    return (
        <>
            <Sidebar cart={null} />
            <div id="content">
                <div
                    className="content-centering"
                    dangerouslySetInnerHTML={{ __html: licenses_content }}
                />
            </div>
        </>
    );
};

const apiBasePath = window.apiBasePath;
const future2 = common.ajax("GET", apiBasePath + "/member/licenses", null);

common.documentLoaded().then(() => {
    const root = document.querySelector("#root") as HTMLElement;

    future2
        .then((response) => {
            const licenses_content: string = response.data;
            root.innerHTML = "";
            render(<LicensesPage licenses_content={licenses_content} />, root);
        })
        .catch((e) => {
            // Probably Unauthorized, redirect to login page.
            if (e.status === UNAUTHORIZED) {
                // Render login
                login.render_login(root, null, null);
            } else {
                UIkit.modal.alert(
                    jsx_to_string(
                        <>
                            <h2>Failed to load member info</h2>
                            <p>{e.toString()}</p>
                        </>,
                    ),
                );
            }
        });
});
