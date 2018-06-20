import React from 'react'
import BackboneTable from '../../../BackboneTable'
import { withRouter } from 'react-router'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 3,
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	removeTextMessage: function(permission)
	{
		return "Are you sure you want to remove permission \"" + permission.title + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.notify("Error deleting permission", {timeout: 0, status: "danger"});
	},

	renderHeader: function()
	{
		return [
			{
				title: "Behörighet",
			},
			{
				title: "",
			},
		];
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td>{row.permission}</td>
			</tr>
		);
	},
}));