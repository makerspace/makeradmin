// Load jQuery and UIkit
global.jQuery = require('jquery')
global.$ = global.jQuery;
require('uikit')
require('uikit/dist/js/core/dropdown')
require('uikit/dist/js/components/pagination')
require('uikit/dist/js/components/autocomplete')

import React from 'react';
import ReactDOM from 'react-dom';
import {
	Router,
	Route,
	IndexRoute,
	IndexRedirect,
	Link,
} from 'react-router'
import Backbone from './Backbone/FullExtend'
import { browserHistory } from 'react-router'
import {
	MemberHandler,
	MemberAddHandler,
} from './Member/Member'
import { MembersHandler } from './Member/Members'
import { GroupHandler, GroupAddHandler, GroupEditHandler } from './Group/Group'
import { GroupsHandler } from './Group/Groups'
import SalesOverviewHandler from './Sales/Overview'
import { SalesProductsHandler } from './Sales/Products'
import { SalesSubscriptionsHandler } from './Sales/Subscriptions'
import { SalesHistoryHandler } from './Sales/History'
import {
	MasterLedgerHandler,
	EconomyOverviewHandler,
	EconomyDebugHandler,
	EconomyAccountingPeriodHandler,
} from './Economy/Other'

import {
	EconomyAccountingInstructionsHandler,
	EconomyAccountingInstructionAddHandler,
	EconomyAccountingInstructionHandler,
	EconomyAccountingInstructionImportHandler,
} from './Economy/Instruction'

import {
	EconomyAccountsHandler,
	EconomyAccountHandler,
	EconomyAccountEditHandler,
	EconomyAccountAddHandler,
} from './Economy/Account'

import EconomyValuationSheetHandler from './Economy/ValuationSheet'
import EconomyResultReportHandler from './Economy/ResultReport'

import {
	EconomyCostCentersHandler,
	EconomyCostCenterHandler,
} from './Economy/CostCenter'

import { InvoiceListHandler, InvoiceHandler, InvoiceAddHandler } from './Economy/Invoice'

import {
	Nav,
	SideNav,
	SideNav2,
	Breadcrumb,
} from './nav'

import SettingsGlobalHandler from './Settings/Global'
import SettingsAutomationHandler from './Settings/Automation'
import StatisticsHandler from './Statistics'
import DashboardHandler from './Dashboard'
import ExportHandler from './Export/Export'

import MailTemplatesHandler from './Mail/Templates'
import MailSendHandler from './Mail/Send'
import { MailHistoryHandler } from './Mail/History'
import KeysOverviewHandler from './Keys/Overview'

import auth from './auth';

var nav = new Backbone.Model({
	brand: "Makerspace Internal v2",
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
			target: "/mail",
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
					target: "/settings/economy/accounts",
				},
				{
					text: "Räkneskapsår",
					target: "/settings/economy/accountingperiods",
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
					text: "Utskick",
					target: "/settings/mail",
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
					target: "/settings/export",
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

class Login extends React.Component
{
	login(e)
	{
		e.preventDefault();

		var username = this.refs.username.value;
		var password = this.refs.password.value;

		auth.login(username, password);
	}

	render()
	{
		return (
			<div className="uk-vertical-align uk-text-center uk-height-1-1">
				<div className="uk-vertical-align-middle" style={{width: "250px"}}>
					<form className="uk-panel uk-panel-box uk-form" onSubmit={this.login.bind(this)}>
						<div className="uk-form-row">
							<h2>Logga in</h2>
						</div>

						<div className="uk-form-row">
							<div className="uk-form-icon">
								<i className="uk-icon-user"></i>
								<input ref="username" className="uk-width-1-1 uk-form-large" type="text" placeholder="Användarnamn" />
							</div>
						</div>

						<div className="uk-form-row">
							<div className="uk-form-icon">
								<i className="uk-icon-lock"></i>
								<input ref="password" className="uk-width-1-1 uk-form-large" type="password" placeholder="Lösenord" />
							</div>
						</div>

						<div className="uk-form-row">
							<button type="submit" className="uk-width-1-1 uk-button uk-button-primary uk-button-large">Logga in</button>
						</div>

						<div className="uk-form-row uk-text-small">
							<a className="uk-float-right uk-link uk-link-muted" onClick={UIkit.modal.alert.bind([], "Haha!")}>Glömt ditt lösenord?</a>
						</div>
					</form>
				</div>
			</div>
		);
	}
}

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
//		auth.login();
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

var NoMatch = React.createClass({
	render: function()
	{
		return (<h2>404</h2>);
	}
});

var NotImplemented = React.createClass({
	render: function()
	{
		return (<h2>Not implemented</h2>);
	}
});

const Logout = React.createClass({
	componentDidMount() {
		auth.logout()
	},

	render() {
		return <p>You are now logged out</p>
	}
})

ReactDOM.render((
	<Router history={browserHistory}>
		<Route path="/" component={App} >
			<IndexRoute component={DashboardHandler} />
			<Route path="logout" component={Logout} />
			<Route path="members">
				<IndexRoute component={MembersHandler} />
				<Route path="add"      component={MemberAddHandler} />
				<Route path=":id"      component={MemberHandler} />
			</Route>
			<Route path="groups">
				<IndexRoute component={GroupsHandler} />
				<Route path="add"      component={GroupAddHandler} />
				<Route path=":id"      component={GroupHandler} />
				<Route path=":id/edit" component={GroupEditHandler} />
			</Route>
			<Route path="keys">
				<IndexRoute component={KeysOverviewHandler} />
			</Route>
			<Route path="sales">
				<IndexRedirect to="overview" />
				<Route path="overview"          component={SalesOverviewHandler} />
				<Route path="products"          component={SalesProductsHandler} />
				<Route path="subscriptions"     component={SalesSubscriptionsHandler} />
				<Route path="history"           component={SalesHistoryHandler} />
			</Route>
			<Route path="economy">
				<IndexRedirect to="overview" />

				<Route path="overview"         component={EconomyOverviewHandler} />
				<Route path="masterledger"     component={MasterLedgerHandler} />

				<Route path="invoice">
					<IndexRedirect to="list" />
					<Route path="list"     component={InvoiceListHandler} />
					<Route path="add"      component={InvoiceAddHandler} />
					<Route path=":id"      component={InvoiceHandler} />
				</Route>

				<Route path="instruction"       component={EconomyAccountingInstructionsHandler} />
				<Route path="instruction/add"   component={EconomyAccountingInstructionAddHandler} />
				<Route path="instruction/:id"   component={EconomyAccountingInstructionHandler} />
				<Route path="instruction/:id/import" component={EconomyAccountingInstructionImportHandler} />

				<Route path="valuationsheet"    component={EconomyValuationSheetHandler} />
				<Route path="resultreport"      component={EconomyResultReportHandler} />

				<Route path="costcenter"        component={EconomyCostCentersHandler} />
				<Route path="costcenter/:id"    component={EconomyCostCenterHandler} />

				<Route path="account/:id"       component={EconomyAccountHandler} />
			</Route>
			<Route path="mail">
				<IndexRoute component={MailHistoryHandler} />
				<Route path="send" component={MailSendHandler} />
			</Route>
			<Route path="statistics"     component={StatisticsHandler} />
			<Route path="settings">
				<IndexRedirect to="global" />
				<Route path="global"     component={SettingsGlobalHandler} />
				<Route path="automation" component={SettingsAutomationHandler} />
				<Route path="export"     component={ExportHandler} />
				<Route path="mail"       component={MailTemplatesHandler} />
				<Route path="economy">
					<Route path="debug"             component={EconomyDebugHandler} />
					<Route path="accountingperiods" component={EconomyAccountingPeriodHandler} />
					<Route path="accounts"          component={EconomyAccountsHandler} />
					<Route path="account/add"       component={EconomyAccountAddHandler} />
					<Route path="account/:id/edit"  component={EconomyAccountEditHandler} />
				</Route>
			</Route>
			<Route path="*" component={NoMatch}/>
		</Route>
	</Router>
), document.getElementById("main"));