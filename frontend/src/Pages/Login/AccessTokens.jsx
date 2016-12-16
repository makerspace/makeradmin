import React from 'react';
import BackboneTable from '../BackboneTable'
import DateTime from '../Formatters/DateTime'
import auth from '../auth'

var AccessTokens = React.createClass(
{
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 4,
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	renderHeader: function()
	{
		return [
			{
				title: "Access token",
			},
			{
				title: "Browser",
			},
			{
				title: "IP-adress",
			},
			{
				title: "Giltig till",
			},
		];
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				{auth.getAccessToken() == row.access_token ?
					<td><i className="uk-icon-check" /> {row.access_token}</td>
				:
					<td>{row.access_token}</td>
				}
				<td>{row.browser}</td>
				<td>{row.ip}</td>
				<td><DateTime date={row.expires} /></td>
			</tr>
		);
	},
});

module.exports = AccessTokens;