import Backbone from 'backbone'
import InstructionModel from '../Models/Instruction'
import config from '../../config'

var InstructionCollection = Backbone.PageableCollection.extend(
{
	model: InstructionModel,
	url: "/economy/" + config.accountingPeriod + "/instruction",
});

module.exports = InstructionCollection;