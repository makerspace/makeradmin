import React from 'react'

// Backbone
import SubscriptionCollection from '../../Collections/Subscription'

import Subscriptions from '../../Components/Tables/Subscriptions'

module.exports =  React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Prenumerationer</h2>
				<p>På denna sida ser du en lista på samtliga prenumerationer.</p>
				<Subscriptions type={SubscriptionCollection} />
			</div>
		);
	},
});
//SalesSubscriptionsHandler.title = "Visa prenumerationer";