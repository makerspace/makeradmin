import React from 'react'

var TableDropdownMenu = React.createClass({
	render: function()
	{
		return(
			<div className="uk-align-right uk-margin-remove">
				<div data-uk-dropdown="{mode:'click'}" className="uk-button-dropdown">
					<button className="uk-button uk-button-mini"><i className="uk-icon-angle-down"></i></button>
					<div className="uk-dropdown uk-dropdown-small">
						<ul className="uk-nav uk-nav-dropdown">
							{React.Children.map(this.props.children, function(child, i) {
								return (<li className="uk-dropdown-close">{child}</li>);
							})}
						</ul>
					</div>
				</div>
			</div>
		);
	}
});

module.exports = TableDropdownMenu;