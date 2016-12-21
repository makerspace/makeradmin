import Backbone from 'backbone'
import InstructionModel from '../Models/Instruction'
import config from '../../config'

var InstructionCollection = Backbone.PageableCollection.extend(
{
	model: InstructionModel,
	url: function()
	{
		return "/economy/" + this.params.period + "/instruction";
	},
});

module.exports = InstructionCollection;