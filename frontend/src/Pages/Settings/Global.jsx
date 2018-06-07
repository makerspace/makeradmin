import React from 'react'

module.exports = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Inställningar</h2>
				<p>Diverse inställningar</p>

				<h3>Aktiverade moduler</h3>
				<ul className="uk-list">
					<li><i className="uk-icon-user" /> Medlemshantering</li>
					<li><i className="uk-icon-group" /> Grupper</li>
					<li><i className="uk-icon-key" /> Nycklar</li>
					<li><i className="uk-icon-shopping-basket" /> Försäljning</li>
					<li><i className="uk-icon-money" /> Ekonomi</li>
					<li><i className="uk-icon-envelope" /> Utskick</li>
					<li><i className="uk-icon-area-chart" /> Statistik</li>
				</ul>
			</div>
		);
	},
});