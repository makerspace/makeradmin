import React from 'react'

var SettingsGlobalHandler = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Inställningar</h2>
				<p>Diverse inställningar</p>

				<h3>Aktiverade moduler</h3>
				<ul className="uk-list">
					<li><i className="uk-icon uk-icon-user" /> Medlemshantering</li>
					<li><i className="uk-icon uk-icon-group" /> Grupper</li>
					<li><i className="uk-icon uk-icon-key" /> Nycklar</li>
					<li><i className="uk-icon uk-icon-shopping-basket" /> Försäljning</li>
					<li><i className="uk-icon uk-icon-money" /> Ekonomi</li>
					<li><i className="uk-icon uk-icon-envelope" /> Utskick</li>
					<li><i className="uk-icon uk-icon-area-chart" /> Statistik</li>
				</ul>
			</div>
		);
	},
});

module.exports = SettingsGlobalHandler