// Load jQuery and UIkit
global.jQuery = require('jquery')
global.$ = global.jQuery;
require('uikit')
require('uikit/dist/js/core/dropdown')
require('uikit/dist/js/components/pagination')
require('uikit/dist/js/components/autocomplete')

// React stuff
import React from 'react';
import ReactDOM from 'react-dom';
import {
	Router,
	browserHistory,
} from 'react-router'
import {
	Nav,
	SideNav,
	SideNav2,
	Breadcrumb,
} from './nav'
import Backbone from './Backbone/FullExtend'

// Login / OAuth
import auth from './auth'
import Login from './Pages/Login/Login'

var nav = new Backbone.Model({
	brand: "MakerAdmin 1.0",
	navItems:
	[
		{
			text: "Medlemmar",
			target: "/members",
			icon: "user",
		},
		{
			text: "Grupper",
			target: "/groups",
			icon: "group",
		},
		{
			text: "Nycklar",
			target: "/keys",
			icon: "key",
		},
		{
			text: "Försäljning",
			target: "/sales",
			icon: "shopping-basket",
			children:
			[
				{
					text: "Översikt",
					target: "/sales/overview",
				},
				{
					text: "Produkter",
					target: "/sales/products",
				},
				{
					text: "Prenumerationer",
					target: "/sales/subscriptions",
				},
				{
					text: "Historik",
					target: "/sales/history",
				},
			],
		},
		{
			text: "Ekonomi",
			target: "/economy",
			icon: "money",
			children:
			[
				{
					text: "Översikt",
					target: "/economy/overview",
				},
				{
					text: "Huvudbok",
					target: "/economy/masterledger",
				},
				{
					text: "Verifikationer",
					target: "/economy/instruction",
					children:
					[
						{
							text: "",
							target: "/economy/instruction/:id",
						},
					],
				},
				{
					text: "Fakturor",
					target: "/economy/invoice",
					children:
					[
						{
							text: "",
							target: "/economy/invoice/:id",
						},
					],
				},
				{
					type: "heading",
					text: "Rapporter",
					target: "",
				},
				{
					text: "Balansrapport",
					target: "/economy/valuationsheet",
				},
				{
					text: "Resultatrapport",
					target: "/economy/resultreport",
				},
				{
					type: "heading",
					text: "Statistik",
					target: "",
				},
				{
					text: "Kostnadsställen",
					target: "/economy/costcenter",
				},
			],
		},
		{
			text: "Utskick",
			target: "/messages",
			icon: "envelope",
		},
		{
			text: "Statistik",
			target: "/statistics",
			icon: "area-chart",
		},
		{
			text: "Inställningar",
			target: "/settings",
			icon: "cog",
			children:
			[
				// Inställningar
				{
					text: "Globala inställningar",
					target: "/settings/global",
				},
				{
					text: "Access tokens",
					target: "/settings/tokens",
				},
				{
					text: "Automation",
					target: "/settings/automation",
				},
				{
					type: "separator",
					target: "",
				},

				// Ekonomi
				{
					type: "heading",
					text: "Ekonomi",
					target: "",
					icon: "money",
				},
				{
					text: "Kontoplan",
					target: "/settings/economy/account",
				},
				{
					text: "Räkneskapsår",
					target: "/settings/economy/accountingperiod",
				},
				{
					text: "Debug",
					target: "/settings/economy/debug",
				},

				// Utskick
				{
					type: "separator",
					target: "",
				},
				{
					type: "heading",
					text: "Utskick",
					target: "",
					icon: "envelope",
				},
				{
					text: "Mallar",
					target: "/settings/mail/templates",
				},
				{
					type: "separator",
					target: "",
				},

				// Export
				{
					type: "heading",
					text: "Export",
					target: "",
					icon: "download",
				},
				{
					text: "Exportera data",
					target: "/settings/export",
				},
				{
					text: "Importera data",
					target: "/settings/import",
				},
			],
		},
		{
			text: "Logga ut",
			target: "/logout",
			icon: "sign-out",
		},
	]
});

var App = React.createClass({
	getInitialState()
	{
		return {
			isLoggedIn: auth.isLoggedIn()
		}
	},

	updateAuth(isLoggedIn)
	{
		this.setState({
			isLoggedIn
		});
	},

	componentWillMount()
	{
		auth.onChange = this.updateAuth;
	},

	render: function()
	{
		if(this.state.isLoggedIn)
		{
			return (
				<div>
					<Nav model={nav} />
					<SideNav model={nav} />

					<div className="uk-container uk-container-center uk-margin-top">
						<div className="uk-grid">
							<div className="uk-width-medium-1-4">
								<SideNav2 model={nav} />
							</div>

							<div className="uk-width-medium-3-4">
								<Breadcrumb routes={this.props.routes}/>
								{this.props.children}
							</div>
						</div>
					</div>
				</div>
			);
		}
		else
		{
			return (
				<Login />
			);
		}

	}
});
App.title = "Internal"

/*
<Route path="tokens"     component={AccessTokensHandler} />
*/

const rootRoute = {
	childRoutes: [
		{
			path: "resetpassword",
			component: require("./Pages/Login/ResetPassword"),
		},
		{
			path: "/",
			component: App,
			indexRoute: {
				component: require("./Pages/Dashboard"),
			},
			childRoutes: [
				{
					path: "logout",
					component: require("./Pages/Login/Logout"),
				},
				require("./Economy/Routes"),
				require("./Membership/Routes"),
				require("./Sales/Routes"),
				require("./Messages/Routes"),
				require("./Keys/Routes"),
				require("./Statistics/Routes"),
				require("./Export/Routes"),
				{
					path: "settings",
					indexRoute: {
						component: require("./Pages/Settings/Global"),
					},
					childRoutes: [
						{
							path: "global",
							indexRoute: {
								component: require("./Pages/Settings/Global"),
							},
						},
						{
							path: "automation",
							indexRoute: {
								component: require("./Pages/Settings/Automation"),
							},
						},
					]
				},
				{
					path: "*",
					component: require("./Pages/404"),
				},
			]
		}
	]
}

ReactDOM.render((
	<Router history={browserHistory} routes={rootRoute} />
), document.getElementById("main"));