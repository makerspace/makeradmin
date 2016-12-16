import React from 'react'

// Backbone
import InvoiceModel from '../../Models/Invoice'

module.exports = React.createClass({
	getInitialState: function()
	{
		var id = this.props.params.id;
		var invoice = new InvoiceModel({id: id});
		invoice.fetch();

		return {
			model: invoice
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Faktura</h2>
				<Invoice model={this.state.model} />
			</div>
		);
	},
});