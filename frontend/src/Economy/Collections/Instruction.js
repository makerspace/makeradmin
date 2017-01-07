import Backbone from 'backbone'
import InstructionModel from '../Models/Instruction'

module.exports = Backbone.PageableCollection.extend(
{
	model: InstructionModel,
	// URL is always provided via the dataSource property in BackboneTable
});