import React from 'react'
import BackboneReact from 'backbone-react-component'
import config from '../../../config'
import { Link } from 'react-router'

// Backbone
import BackboneTable from '../../../BackboneTable'

module.exports = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 5,
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	renderHeader: function ()
	{
		return [
			{
				title: "Medlem",
			},
			{
				title: "MultiAccess",
			},
			{
				title: "Felmeddelande",
			},
		];
	},

	renderRow: function (row, i)
	{
		return (
			<tr key={i}>
				<td>
					{row.member.member_id ?
						<Link to={"/membership/members/" + row.member.member_id}>{row.member.member_number} {row.member.firstname} {row.member.lastname}</Link>
					:
						""
					}
				</td>
				<td>{row.multiaccess_key.member_number}</td>
				<td>{row.errors.map(function(x) { return x + ", "; })}</td>
			</tr>
		);
	},
});