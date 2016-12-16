import React from 'react'

// Backbone
import InvoiceModel from '../../Models/Invoice'

import Invoice from '../../Invoice'

module.exports = React.createClass({
	getInitialState: function()
	{
		var invoice = new InvoiceModel();

		return {
			model: invoice
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Skapa faktura</h2>
				<Invoice model={this.state.model} />
			</div>
		);
	},
});