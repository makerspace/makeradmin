import React from 'react'
import BackboneReact from 'backbone-react-component'
import { Link } from 'react-router'

// Backbone
import BackboneTable from '../../../BackboneTable'

module.exports = React.createClass({
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

	renderHeader: function ()
	{
		return [
			{
				title: "Tictail",
			},
			{
				title: "Local storage",
			},
			{
				title: "Medlem",
			},
			{
				title: "Verifikation",
			},
		];
	},

	renderRow: function (row, i)
	{
		/*
		Modes:
			1 = Samtliga
			2 = Saknar relation till verifikation
			3 = Har relation till verifikation
			4 = Saknar relation till member
			5 = Har relation till member
			6 = Saknar relation till member eller verifikation
		*/
		var mode = 6;

		if(mode == 1)
		{
		}
		else if(mode == 2 && row.instruction_number != "")
		{
			return;
		}
		else if(mode == 3 && row.instruction_number == "")
		{
			return;
		}
		else if(mode == 4 && row.member_id != "")
		{
			return;
		}
		else if(mode == 5 && row.member_id == "")
		{
			return;
		}
		else if(mode == 6 && row.member_id != "" && row.instruction_number != "")
		{
			return;
		}

		return (
			<tr key={i}>
				<td><a target="_blank" href={"https://tictail.com/dashboard/store/makerspace/settings/orders/" + row.tictail_id}>{row.tictail_id}</a></td>
				<td><a target="_blank" href={config.apiBasePath + "/tictail/order/" + row.tictail_id}>{row.tictail_id}.json</a></td>
				<td><Link to={"/membership/members/" + row.member_id}>{row.member_id}</Link></td>
				<td>
					{row.instruction_number ?
						// TODO: Not hardcoded accounting period
						<Link to={"/economy/2016/instruction/" + row.instruction_number}>{row.instruction_number}</Link>
					:
						<a target="_blank" href={config.apiBasePath + "/auto/createinstruction/" + row.tictail_id}>Skapa verifikation</a>
					}
				</td>
			</tr>
		);
	},
});