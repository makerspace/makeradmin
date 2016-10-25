import React from 'react'

// Backbone
import TransactionCollection from '../Backbone/Collections/Transaction'

import TransactionsUser from './TransactionsUser'

var TransactionUserBox = React.createClass(
{
	render: function()
	{
		return (
			<div>
				<TransactionsUser type={TransactionCollection}
					filters={{
						relations:
						[
							{
								type: "member",
								member_number: this.props.member_number,
							}
						]
					}}
				/>
			</div>
		);
	},
});

module.exports = TransactionUserBox