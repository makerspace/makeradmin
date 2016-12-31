import React from 'react'

// Backbone
import KeysCollection from '../Collections/Keys'

import Keys from '../Components/Tables/Keys'
import TableFilterBox from '../../TableFilterBox'
import { Link } from 'react-router'

module.exports = React.createClass({
	getInitialState: function()
	{
		return {
			filters: {},
		};
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

				<p className="uk-float-left">Visa lista över samtliga nycklas i systemet</p>
				<Link to="/keys/add" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"></i> Lägg till nyckel</Link>

				<TableFilterBox onChange={this.updateFilters} />
				<Keys
					type={KeysCollection}
					filters={this.state.filters}
				/>
			</div>
		);
	},
});
//KeysOverviewHandler.title = "Nycklar";