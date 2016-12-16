import React from 'react'

module.exports = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Översikt</h2>
				<ul>
					<li>Samtliga obetalda fakturor + 3 senaste betalda</li>
					<li>5 senaste skapade/ändrade verifikationerna</li>
					<li>Saldo på konton (Bank, Stripe, PayPal, etc)</li>
					<li>Datum för senaste synkroniseringar (Bank, Stripe, PayPal, etc)</li>
				</ul>
			</div>
		);
	},
});