import React from 'react'

// Backbone
import CostCenterModel from '../Backbone/Models/CostCenter'

var EconomyCostCenterHandler = React.createClass({
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

module.exports = EconomyCostCenterHandler;