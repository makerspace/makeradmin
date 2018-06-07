import React from 'react'

// Backbone
import SubscriptionCollection from '../../../Collections/Subscription'

import SubscriptionsUser from '../../../Components/Tables/SubscriptionsUser'

module.exports = React.createClass(
{
	render: function()
	{
		return (
			<SubscriptionsUser
				type={SubscriptionCollection}
				dataSource={{
					url: "/related",
					params: {
						param: "/membership/member/" + this.props.params.member_id,
						matchUrl: "/sales/subscription/(.*)",
						from: "sales/subscription",
					}
				}}
			/>
		);
	},
});