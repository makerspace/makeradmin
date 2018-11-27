import React from 'react';

// Get versions of dependencies
const ReactVersion    = require("../../node_modules/react/package.json").version;
const JqueryVersion = require("../../node_modules/jquery/package.json").version;
const UikitVersion = require("../../node_modules/uikit/package.json").version;
const ReactRouterVersion = require("../../node_modules/react-router/package.json").version;
const ReactSelectVersion = require("../../node_modules/react-select/package.json").version;
const ReactDomVersion = require("../../node_modules/react-dom/package.json").version;


export default () => {
    return (
        <div>
            <h2>Build</h2>
            <dl>
                <dt>Build date:</dt>
                <dd>{__BUILD_DATE__}</dd>

                <dt>Build hash:</dt>
                <dd>{__COMMIT_HASH__}</dd>
            </dl>

            <h2>API</h2>
            <dl>
                <dt>API Version:</dt>
                <dd>{config.apiVersion}</dd>

                <dt>API endpoint:</dt>
                <dd>{config.apiBasePath}</dd>
            </dl>

            <h2>Included dependencies:</h2>
            <dl>
                <dt>React version:</dt>
                <dd>{ReactVersion}</dd>

                <dt>jQuery version:</dt>
                <dd>{JqueryVersion}</dd>

                <dt>uikit version:</dt>
                <dd>{UikitVersion}</dd>

                <dt>react-router version:</dt>
                <dd>{ReactRouterVersion}</dd>

                <dt>react-select version:</dt>
                <dd>{ReactSelectVersion}</dd>

                <dt>react-dom version:</dt>
                <dd>{ReactDomVersion}</dd>
            </dl>

            <h2>License</h2>
            <p>GPL version 3</p>
        </div>
    );
};