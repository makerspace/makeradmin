import React from 'react'
import BackboneReact from 'backbone-react-component'

// Backbone
import GroupCollection from '../Backbone/Collections/Group'

import { Link } from 'react-router'
import BackboneTable from '../BackboneTable'
import TableDropdownMenu from '../TableDropdownMenu'

import TableFilterBox from '../TableFilterBox'

var GroupsHandler = React.createClass({
	getInitialState: function()
	{
		return {
			filters: {},
		};
	},

	// TODO: Remove?
	overrideFiltersFromProps: function(filters)
	{
		console.log("overrideFiltersFromProps");
		return filters;
	},

	updateFilters: function(newFilter)
	{
		var filters = this.overrideFiltersFromProps(newFilter);
		this.setState({
			filters: filters
		});
	},

	render: function()
	{
		return (
			<div>
				<h2>Grupper</h2>

				<p className="uk-float-left">På denna sida ser du en lista på samtliga grupper.</p>
				<Link className="uk-button uk-button-primary uk-float-right" to="/groups/add"><i className="uk-icon-plus-circle"></i> Skapa ny grupp</Link>

				<TableFilterBox onChange={this.updateFilters} />
				<Groups type={GroupCollection} filters={this.state.filters} />
			</div>
		);
	},
});
GroupsHandler.title = "Visa grupper";

var Groups = React.createClass({
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

	removeTextMessage: function(entity)
	{
		return "Are you sure you want to remove group \"" + entity.title + "\"?";
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
				<td><Link to={"/groups/" + row.entity_id}>{row.title}</Link></td>
				<td><Link to={"/groups/" + row.entity_id}>{row.description}</Link></td>
				<td>{row.membercount}</td>
				<td>
					<TableDropdownMenu>
						<Link to={"/groups/" + row.entity_id + "/edit"}><i className="uk-icon uk-icon-cog"></i> Redigera grupp</Link>
						{this.removeButton(i, "Ta bort grupp")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});

module.exports = {
	GroupsHandler,
	Groups
}