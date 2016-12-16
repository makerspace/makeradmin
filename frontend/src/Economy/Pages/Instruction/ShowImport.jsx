import React from 'react'

// Backbone
import InstructionModel from '../../Models/Instruction'

module.exports = React.createClass({
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
		return <EconomyAccountingInstructionImport model={this.state.model} />
	}
});