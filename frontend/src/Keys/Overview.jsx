import React from 'react'

// Backbone
import RfidCollection from '../Backbone/Collections/Rfid'

import Keys from './Keys'
import TableFilterBox from '../TableFilterBox'

var KeysOverviewHandler = React.createClass({
	getInitialState: function()
	{
		return {
			filters: {},
		};
	},

	edit: function(entity)
	{
		UIkit.modal.alert("TODO: Parent edit" + entity);
	},

	overrideFiltersFromProps: function(filters)
	{
		console.log("overrideFiltersFromProps");

		if(this.props.member_number !== undefined && this.props.member_number.length > 0)
		{
			console.log("  member_number present");

			if(!filters.relations)
			{
				filters.relations = [];
			}

			filters.relations.push({
				type: "member",
				member_number: this.props.member_number,
			});
		}

		return filters;
	},

	updateFilters: function(newFilter)
	{
		var filters = this.overrideFiltersFromProps(newFilter);
		this.setState({
			filters: filters
		});
	},

	componentWillReceiveProps: function(nextProps)
	{
		console.log("componentWillReceiveProps");
		if(nextProps.member_number != this.props.member_number)
		{
			console.log("TODO: Filter on member number");
			this.props.member_number = nextProps.member_number;

			var filters = this.overrideFiltersFromProps(this.state.filters);
			this.setState({
				filters: filters
			});
		}
		else
		{
			console.log("TODO: Turn off filter on member number");
		}
	},

	render: function()
	{
		return (
			<div>
				<h2>Nycklar</h2>
				<p>Visa lista över samtliga nycklas i systemet</p>
				<TableFilterBox onChange={this.updateFilters} />
				<Keys type={RfidCollection} edit={this.edit} filters={this.state.filters} />
			</div>
		);
	},
});
KeysOverviewHandler.title = "Nycklar";

module.exports = KeysOverviewHandler