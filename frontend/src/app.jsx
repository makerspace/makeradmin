// Load jQuery and UIkit
global.jQuery = require('jquery')
global.$ = global.jQuery;
require('uikit')
require('uikit/dist/js/core/dropdown')
require('uikit/dist/js/components/pagination')
require('uikit/dist/js/components/autocomplete')
require('uikit/dist/js/components/notify')
require('uikit/dist/js/components/upload')

// React stuff
import React from 'react';
import ReactDOM from 'react-dom';
import {Router,	browserHistory} from 'react-router';
import {Nav, SideNav, SideNav2, Breadcrumb} from './nav';
import Backbone from './Backbone/FullExtend';

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
					text: "Produkter",
					target: "/sales/product",
				},
				{
					text: "Ordrar",
					target: "/sales/order",
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
				{
					text: "About",
					target: "/settings/about",
				},
				{
					text: "Access tokens",
					target: "/settings/tokens",
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

const App = React.createClass({
	getInitialState()
	{
		return {
			isLoggedIn: auth.isLoggedIn()
		};
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

		return (
			<Login />
		);

	}
});
App.title = "Internal";

const rootRoute = {
	childRoutes: [
		{
			path: "member",
			indexRoute: {
				component: require("./User/Member"),
			},
			childRoutes: [
				{
					path: "login/:token",
					component: require("./User/Login"),
				}
			]
		},
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
				require("./Membership/Routes"),
				require("./Sales/Routes"),
				require("./Messages/Routes"),
				require("./Keys/Routes"),
				require("./Statistics/Routes"),
				require("./Tictail/Routes"),
				{
					path: "settings",
					indexRoute: {
						component: require("./Pages/About"),
					},
					childRoutes: [
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
};


ReactDOM.render((
	<Router history={browserHistory} routes={rootRoute} />
), document.getElementById("main"));
