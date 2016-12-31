import React from 'react'

// Backbone
import SalesHistoryCollection from '../Collections/SalesHistory'
import SalesHistoryModel from '../Models/SalesHistory'

import TableFilterBox from '../../TableFilterBox'
import History from '../Components/Tables/History'

module.exports = React.createClass({
	getInitialState: function()
	{
		return {
			filters: this.props.filters || {},
		};
	},

	updateFilters: function(newFilter)
	{
		var filters = this.overrideFiltersFromProps(newFilter);
		this.setState({
			filters: filters
		});
	},

	overrideFiltersFromProps: function(filters)
	{
		return filters;
	},

	render: function()
	{
		return (
			<div>
				<h2>Försäljningshistorik</h2>
				<p>På denna sida ser du en lista på samtliga sålda produkter.</p>
				<TableFilterBox onChange={this.updateFilters} />
				<History type={SalesHistoryCollection} filters={this.state.filters} />
			</div>
		);
	},
});
//SalesHistoryHandler.title = "Visa försäljning";