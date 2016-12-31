import React from 'react'

// Backbone
import InvoiceCollection from '../../Collections/Invoice'

import { Link } from 'react-router'
import TableFilterBox from '../../../TableFilterBox'

import InvoiceList from '../../Components/Tables/InvoiceList'

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
			<div className="uk-width-1-1">
				<h2>Fakturor</h2>

				<p className="uk-float-left">På denna sida ser du en lista på samtliga fakturor för det valda bokföringsåret.</p>
				<Link to={"/economy/" + this.props.params.period + "/invoice/add"} className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"></i> Skapa ny faktura</Link>

				<TableFilterBox onChange={this.updateFilters} />
				<InvoiceList
					type={InvoiceCollection}
					filters={this.state.filters}
					dataSource={{
						url: "/economy/" + this.props.params.period + "/invoice/"
					}}
				/>
			</div>
		);
	},
});
//InvoiceListHandler.title = "Visa fakturor";