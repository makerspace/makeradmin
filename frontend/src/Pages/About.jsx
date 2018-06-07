import React from 'react'

// Get versions of dependencies
const ReactVersion    = require("json-loader!../../node_modules/react/package.json").version;
const JqueryVersion = require("json-loader!../../node_modules/jquery/package.json").version;
const UikitVersion = require("json-loader!../../node_modules/uikit/package.json").version;
const BackboneVersion = require("json-loader!../../node_modules/backbone/package.json").version;
const BackboneReactVersion = require("json-loader!../../node_modules/backbone-react-component//package.json").version;
const BackbonePaginatorVersion = require("json-loader!../../node_modules/backbone.paginator//package.json").version;
const ReactRouterVersion = require("json-loader!../../node_modules/react-router/package.json").version;
const ReactSelectVersion = require("json-loader!../../node_modules/react-select/package.json").version;
const ReactDomVersion = require("json-loader!../../node_modules/react-dom/package.json").version;

module.exports = React.createClass({
	render: function ()
	{
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

					<dt>Backbone version:</dt>
					<dd>{BackboneVersion}</dd>

					<dt>backbone-react-component version:</dt>
					<dd>{BackboneReactVersion}</dd>

					<dt>backbone.paginator version:</dt>
					<dd>{BackbonePaginatorVersion}</dd>

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
	}
});