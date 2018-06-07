import React from 'react'
import BackboneReact from 'backbone-react-component'
import BackboneTable from '../../BackboneTable'

// Backbone
import MasterledgerCollection from '../Collections/Masterledger'

import { Link } from 'react-router'
import Currency from '../../Components/Currency'
import EconomyAccounts from '../Components/Tables/Masterledger'

module.exports = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Huvudbok</h2>
				<EconomyAccounts
					type={MasterledgerCollection}
					dataSource={{
						url: "/economy/" + this.props.params.period + "/masterledger",
					}}
				/>
			</div>
		);
	},
});