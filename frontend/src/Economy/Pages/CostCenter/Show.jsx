import React from 'react'

// Backbone
import CostCenterModel from '../../Models/CostCenter'

import EconomyCostCenter from '../../Components/Forms/CostCenter'

module.exports = React.createClass({
	getInitialState: function()
	{
		var id = this.props.params.id;

		var costcenter = new CostCenterModel({id: id});
		costcenter.fetch();

		return {
			model: costcenter
		};
	},

	render: function()
	{
		return (<EconomyCostCenter model={this.state.model} />);
	}
});