import React from 'react'

// Backbone
import OrderCollection from '../../Collections/Order'

import TableFilterBox from '../../../TableFilterBox'
import Orders from '../../Components/Tables/Orders'

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
				<h2>Inkommna ordrar</h2>
				<TableFilterBox onChange={this.updateFilters} />
				<Orders type={OrderCollection} filters={this.state.filters} />
			</div>
		);
	},
});
