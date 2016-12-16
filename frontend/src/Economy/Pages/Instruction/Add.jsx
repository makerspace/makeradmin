import React from 'react'

// Backbone
import InstructionModel from '../../Models/Instruction'

import EconomyAccountingInstruction from '../../Instruction'

module.exports = React.createClass({
	getInitialState: function()
	{
		var instruction = new InstructionModel();

		return {
			model: instruction
		};
	},

	render: function()
	{
		return (<EconomyAccountingInstruction model={this.state.model} />);
	}
});