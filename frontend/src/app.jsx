// Load jQuery and UIkit
global.jQuery = require('jquery')
global.$ = global.jQuery;
require('uikit')
require('uikit/dist/js/core/dropdown')
require('uikit/dist/js/components/pagination')
require('uikit/dist/js/components/autocomplete')
require('uikit/dist/js/components/notify')

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
			target: "/membership",
			icon: "user",
			children:
			[
				{
					text: "Medlemmar",
					target: "/membership/members",
					icon: "user",
				},
				{
					text: "Grupper",
					target: "/membership/groups",
					icon: "group",
				},
			],
		},
		{
			text: "Automation",
			target: "/auto",
			icon: "coffee",
			children:
			[
				{
					text: "Översikt",
					target: "/auto/overview",
				},
				{
					type: "separator",
				},
				{
					text: "Tictail-ordrar",
					target: "/auto/tictail",
				},
				{
					text: "Skapa verifikationer",
					target: "/auto/verification",
				},
				{
					text: "Multiaccess",
					target: "/auto/multiaccess",
				},
			],
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
					target: "/sales/product",
				},
				{
					text: "Prenumerationer",
					target: "/sales/subscription",
				},
				{
					text: "Historik",
					target: "/sales/history",
				},
			],
		},
		{
			text: "Ekonomi",
			target: "/economy/2016",
			icon: "money",
			children:
			[
				{
					text: "Översikt",
					target: "/economy/2016/overview",
				},
				{
					text: "Huvudbok",
					target: "/economy/2016/masterledger",
				},
				{
					text: "Verifikationer",
					target: "/economy/2016/instruction",
					children:
					[
						{
							text: "",
							target: "/economy/2016/instruction/:id",
						},
					],
				},
				{
					text: "Fakturor",
					target: "/economy/2016/invoice",
					children:
					[
						{
							text: "",
							target: "/economy/2016/invoice/:id",
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
					target: "/economy/2016/valuationsheet",
				},
				{
					text: "Resultatrapport",
					target: "/economy/2016/resultreport",
				},
				{
					type: "heading",
					text: "Statistik",
					target: "",
				},
				{
					text: "Kostnadsställen",
					target: "/economy/2016/costcenter",
				},
			],
		},
		{
			text: "Utskick",
			target: "/messages",
			icon: "envelope",
			children: [
				{
					text: "Historik",
					target: "/messages/history",
					icon: "list",
				},
				{
					text: "Nytt utskick",
					target: "/messages/new",
					icon: "envelope",
				},
				{
					text: "Mallar",
					target: "/messages/templates",
					icon: "file-text-o",
				},
			],
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

				// About
				{
					type: "heading",
					text: "About",
					target: "",
					icon: "about",
				},
				{
					text: "About",
					target: "/settings/about",
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
				require("./Tictail/Routes"),
				require("./Auto/Routes"),
				{
					path: "settings",
					indexRoute: {
						component: require("./Pages/Settings/Global"),
					},
					childRoutes: [
						{
							path: "global",
							component: require("./Pages/Settings/Global"),
						},
						{
							path: "automation",
							component: require("./Pages/Settings/Automation"),
						},
						{
							path: "tokens",
							component: require("./Pages/Login/AccessTokens"),
						},
						{
							path: "about",
							component: require("./Pages/About"),
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