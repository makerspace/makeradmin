import React from 'react'

// Backbone
import InstructionModel from '../../Models/Instruction'

import EconomyAccountingInstructionImport from '../../Components/InstructionImport'

module.exports = React.createClass({
	getInitialState: function()
	{
		var instruction = new InstructionModel({
			period: this.props.params.period,
			instruction_number: this.props.params.instruction_number
		});
		instruction.fetch();

		return {
			model: instruction
		};
	},

	render: function()
	{
		return <EconomyAccountingInstructionImport model={this.state.model} />
	}
});