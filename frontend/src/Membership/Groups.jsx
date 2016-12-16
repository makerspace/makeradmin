import React from 'react'
import BackboneReact from 'backbone-react-component'

import { Link } from 'react-router'
import BackboneTable from '../BackboneTable'
import TableDropdownMenu from '../TableDropdownMenu'

module.exports = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 9,
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	componentWillReceiveProps: function(nextProps)
	{
		if(nextProps.filters != this.state.filters)
		{
			this.setState({
				filters: nextProps.filters
			});

			// TODO: setState() has a delay so we need to wait a moment
			var _this = this;
			setTimeout(function() {
				_this.fetch();
			}, 100);
		}
	},

	removeTextMessage: function(group)
	{
		return "Are you sure you want to remove group \"" + group.title + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.modal.alert("Error deleting group");
	},

	renderHeader: function()
	{
		return [
			{
				title: "Namn",
				sort: "title",
			},
			{
				title: "Beskrivning",
				sort: "description",
			},
			{
				title: "Antal medlemmar",
				sort: "membercount",
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
				<td><Link to={"/groups/" + row.group_id}>{row.title}</Link></td>
				<td><Link to={"/groups/" + row.group_id}>{row.description}</Link></td>
				<td>{row.membercount}</td>
				<td>
					<TableDropdownMenu>
						<Link to={"/groups/" + row.group_id + "/edit"}><i className="uk-icon uk-icon-cog"></i> Redigera grupp</Link>
						{this.removeButton(i, "Ta bort grupp")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});