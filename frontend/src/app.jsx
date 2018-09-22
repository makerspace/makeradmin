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
import {Nav, SideNav} from './nav';
import Backbone from './Backbone/FullExtend';

// Login / OAuth
import auth from './auth';
import Login from './Pages/Login/Login'

const nav = new Backbone.Model({
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
				{
					text: "Nycklar",
					target: "/membership/keys",
					icon: "key",
				},
						{
					text: "Medlemsperioder",
					target: "/membership/spans",
					icon: "clock-o",
				},
			],
		},
		{
			text: "Försäljning",
			target: "/sales",
			icon: "shopping-basket",
			children:
			[
				{
					text: "Ordrar",
					target: "/sales/order",
				},
				{
					text: "Produkter",
					target: "/sales/product",
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
					<div className="uk-container uk-container-center uk-margin-top">
						<div className="uk-grid">
							<div className="uk-width-medium-1-4">
								<SideNav model={nav} />
							</div>

							<div className="uk-width-medium-3-4">
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
App.title = "MakerAdmin";

const rootRoute = {
    childRoutes: [
        require("./User/Routes"),
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
                require("./Statistics/Routes"),
                require("./Settings/Routes"),
				{
					path: "*",
					component: require("./Pages/404"),
				},
			]
		}
	]
};


ReactDOM.render(<Router history={browserHistory} routes={rootRoute} />, document.getElementById("main"));
