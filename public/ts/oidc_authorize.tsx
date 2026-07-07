import { render } from "preact";
import * as common from "./common";
import { UNAUTHORIZED } from "./common";
import * as login from "./login";
import { Sidebar } from "./sidebar";

type AuthorizeParams = {
    client_id: string;
    redirect_uri: string;
    state: string | null;
    response_type: string | null;
    scope: string | null;
};

function parseParams(): AuthorizeParams | null {
    const query = new URLSearchParams(window.location.search);
    const client_id = query.get("client_id");
    const redirect_uri = query.get("redirect_uri");
    if (!client_id || !redirect_uri) {
        return null;
    }
    return {
        client_id,
        redirect_uri,
        state: query.get("state"),
        response_type: query.get("response_type"),
        scope: query.get("scope"),
    };
}

function clientDisplayName(client_id: string): string {
    return client_id.charAt(0).toUpperCase() + client_id.slice(1);
}

const StatusPage = ({
    title,
    message,
    spinner,
}: {
    title: string;
    message: string;
    spinner?: boolean;
}) => (
    <>
        <Sidebar cart={null} />
        <div id="content">
            <div class="content-centering">
                <div class="uk-width-medium" style="text-align: center;">
                    <h1>{title}</h1>
                    {spinner ? <div uk-spinner="ratio: 2" /> : null}
                    <p>{message}</p>
                </div>
            </div>
        </div>
    </>
);

common.documentLoaded().then(() => {
    const root = document.querySelector("#root") as HTMLElement;
    const apiBasePath = window.apiBasePath;
    const params = parseParams();

    if (root == null) {
        return;
    }

    if (params == null) {
        render(
            <StatusPage
                title="Ogiltig förfrågan"
                message="Länken saknar nödvändiga parametrar (client_id, redirect_uri)."
            />,
            root,
        );
        return;
    }

    const clientName = clientDisplayName(params.client_id);

    render(
        <StatusPage
            title={`Fortsätter till ${clientName}`}
            message="Ett ögonblick..."
            spinner
        />,
        root,
    );

    common
        .ajax("POST", apiBasePath + "/oidc/authorize", {
            client_id: params.client_id,
            redirect_uri: params.redirect_uri,
            state: params.state,
            response_type: params.response_type,
            scope: params.scope,
        })
        .then((json) => {
            window.location.replace(json.data.redirect);
        })
        .catch((e) => {
            if (e.status === UNAUTHORIZED) {
                // Not logged in (or expired token): show the ordinary login
                // page and come back here afterwards to finish the flow.
                common.removeToken();
                login.render_login(
                    root,
                    `Logga in för att fortsätta till ${clientName}`,
                    window.location.href,
                );
            } else {
                render(
                    <StatusPage
                        title="Inloggningen misslyckades"
                        message={
                            e.message ||
                            `Kunde inte logga in till ${clientName}.`
                        }
                    />,
                    root,
                );
            }
        });
});
