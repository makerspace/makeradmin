import React from 'react'

// Backbone
import InstructionModel from '../Backbone/Models/Instruction'

import EconomyAccountingInstruction from './Instruction'
var EconomyAccountingInstructionAddHandler = React.createClass({
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

module.exports = EconomyAccountingInstructionAddHandler