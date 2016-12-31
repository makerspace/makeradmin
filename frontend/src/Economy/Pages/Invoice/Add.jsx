import React from 'react'

// Backbone
import InvoiceModel from '../../Models/Invoice'

import Invoice from '../../Components/Forms/Invoice'

module.exports = React.createClass({
	getInitialState: function()
	{
		return {
			model: new InvoiceModel()
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