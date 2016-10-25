import React from 'react'
import {
	Link,
	IndexLink,
	withRouter,
} from 'react-router'
import BackboneReact from 'backbone-react-component'

var NavItem = React.createClass({
	contextTypes: {
		history: React.PropTypes.object
	},

	render: function()
	{
		if(this.props.navItem.external)
		{
			return (
				<li>
					<a href={this.props.navItem.target}>{this.props.navItem.text}</a>
				</li>
			);
		}
		else
		{
			if(this.context.history.isActive(this.props.navItem.target))
			{
				var className = "uk-active";
			}
			else
			{
				var className = null;
			}

			return (
				<li className={className}>
					<IndexLink activeClassName="uk-active" to={this.props.navItem.target}>
						<i className={"uk-icon-" + this.props.navItem.icon}></i>
						&nbsp;
						{this.props.navItem.text}
					</IndexLink>
				</li>
			);
		}
	}
});

var Nav = React.createClass({
	mixins: [Backbone.React.Component.mixin],

	contextTypes: {
		history: React.PropTypes.object
	},

	render: function ()
	{
		return (
			<nav className="uk-navbar">
				<div className="uk-container uk-container-center">
					<Link to="/" className="uk-navbar-brand">{this.state.model.brand}</Link>
					<ul className="uk-navbar-nav uk-hidden-small uk-navbar-attached">
						{this.state.model.navItems.map(function (navItem, i) {
							return (<NavItem navItem={navItem} key={i} />);
						})}
					</ul>
					<div className="uk-navbar-flip">
						<a className="uk-navbar-toggle uk-visible-small" data-uk-offcanvas="{target:'#sidenav'}"></a>
					</div>
				</div>
			</nav>
		);
	}
});

var SideNav = React.createClass({
	mixins: [Backbone.React.Component.mixin],

	render: function ()
	{
		return (
			<div id="sidenav" className="uk-offcanvas">
				<div className="uk-offcanvas-bar">
					<ul className="uk-nav uk-nav-offcanvas" data-uk-nav>
						<li><IndexLink to="/">{this.state.model.brand}</IndexLink></li>
						{this.state.model.navItems.map(function (navItem, i) {
							return (<NavItem navItem={navItem} key={i} />);
						})}
					</ul>
				</div>
			</div>
		);
	}
})

var SideNav2 = React.createClass({
	mixins: [Backbone.React.Component.mixin],

	contextTypes: {
		history: React.PropTypes.object
	},

	render: function ()
	{
		// Get the main category (level 0)
		var activeItem = null;
		for(var i = 0; i < this.state.model.navItems.length; i++)
		{
			var item = this.state.model.navItems[i];
			if(this.context.history.isActive(item.target))
			{
				activeItem = item;
			}
		}

		// There is no active menu, or children.
		if(activeItem === null || typeof activeItem.children == 'undefined')
		{
			return false;
		}
		else
		{
			return (
				<div className="uk-panel uk-panel-box" data-uk-sticky="{top:35}">
					<ul className="uk-nav uk-nav-side" data-uk-scrollspy-nav="{closest:'li', smoothscroll:true}">
						<li className="uk-nav-header">{activeItem.text}</li>
						<li className="uk-nav-divider"></li>
						{activeItem.children.map(function (navItem, i) {
							if(typeof navItem.type != "undefined" && navItem.type == "separator")
							{
								return (<li key={i} className="uk-nav-divider"></li>);
							}
							else if(typeof navItem.type != "undefined" && navItem.type == "heading")
							{
								return (<li key={i} className="uk-nav-header">{navItem.text}</li>);
							}
							else
							{
								return (<NavItem key={i} navItem={navItem} activeItem={activeItem} />);
							}
						})}
					</ul>
				</div>
			);
		}
	},
});

var Breadcrumb = React.createClass({
	render: function ()
	{
//		const depth = this.props.routes.length;
return (<span></span>);
		return (
			<ul className="uk-breadcrumb">
				{this.props.routes.map((item, index) =>
					<li key={index}>
						<Link
							onlyActiveOnIndex={true}
							activeClassName="uk-active"
							to={item.path || ''}>
							{item.component.title}
						</Link>
					</li>
				)}
			</ul>
		);
	},
});

module.exports = { Nav, SideNav, SideNav2, Breadcrumb }