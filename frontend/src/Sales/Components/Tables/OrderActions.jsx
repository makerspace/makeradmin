import React from 'react'

import BackboneTable from '../../../BackboneTable'
import { withRouter } from 'react-router'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 6,
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
				title: "Rad",
				class: "uk-text-right",
			},
			{
				title: "Orderrad",
			},
			{
				title: "Åtgärd",
			},
			{
				title: "Antal",
				class: "uk-text-right",
			},
			{
				title: "Utförd",
				class: "uk-text-right",
			},
		];
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td className="uk-text-right">{i+1}</td>
				<td>{row.content_id}</td>
				<td>{row.action}</td>
				<td className="uk-text-right">{row.value}</td>
				<td className="uk-text-right">{row.completed_at ? row.completed_at : 'pending'}</td>
			</tr>
		);
	},
}));