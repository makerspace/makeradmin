import Backbone from 'backbone'

var InstructionModel = Backbone.Model.fullExtend(
{
	idAttribute: "instruction_number",
	urlRoot: "/economy/2015/instruction",
	defaults: {
		entity_id: 0,
		instruction_number: 0,
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		accounting_date: "0000-00-00T00:00:00Z",
		importer: "",
		external_id: "",
		external_date: "",
		external_data: "",
		description: "",
		transactions: [],
		files: [],
		balance: 0,
	},
});

module.exports = InstructionModel;