import React from 'react';

import {Link, IndexLink, withRouter} from 'react-router';
import BackboneReact from 'backbone-react-component'


const NavItem = withRouter(props => {
    const {navItem, router} = props;
    const {target, text, icon} = navItem;
    
    return (
        <li className={router.isActive(target) ? "uk-active" : null}>
            <IndexLink activeClassName="uk-active" to={target}>
                <i className={"uk-icon-" + icon}/>&nbsp;{text}
            </IndexLink>
        </li>
    );
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
				</div>
			</nav>
		);
	}
});

var SideNav = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin],

	render: function ()
	{
		// Get the main category (level 0)
		var activeItem = null;
		for(var i = 0; i < this.state.model.navItems.length; i++)
		{
			var item = this.state.model.navItems[i];
			if(this.props.router.isActive(item.target))
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
}));

module.exports = { Nav, SideNav }