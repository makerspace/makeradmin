import React from 'react'

// Backbone
import InstructionModel from '../Backbone/Models/Instruction'

import EconomyAccountingInstruction from './Instruction'

var EconomyAccountingInstructionHandler = React.createClass({
	getInitialState: function()
	{
		var instruction = new InstructionModel({instruction_number: this.props.params.id});
		instruction.fetch();

		return {
			model: instruction
		};
	},

	render: function()
	{
		return (<EconomyAccountingInstruction model={this.state.model} />);
	}
});

module.exports = EconomyAccountingInstructionHandler