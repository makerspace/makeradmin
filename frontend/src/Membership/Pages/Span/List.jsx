import React from 'react'

// Backbone
import SpanCollection from '../../Collections/Span'

import TableFilterBox from '../../../TableFilterBox'

import Spans from '../../Components/Tables/Spans'

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
				<h2>Medlemsperioder</h2>

				<p className="uk-float-left">På denna sida ser du en lista på samtliga medlemsperioder.</p>

				<TableFilterBox onChange={this.updateFilters} />
				<Spans type={SpanCollection} filters={this.state.filters} />
			</div>
		);
	},
});