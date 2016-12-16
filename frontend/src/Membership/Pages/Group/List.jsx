import React from 'react'

// Backbone
import GroupCollection from '../../Collections/Group'

import Groups from '../../Groups'

import { Link } from 'react-router'

import TableFilterBox from '../../../TableFilterBox'

module.exports = React.createClass({
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
//GroupsHandler.title = "Visa grupper";