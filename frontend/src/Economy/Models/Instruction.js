import Backbone from 'backbone'
import config from '../../config'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "instruction_number",
	urlRoot: function()
	{
		return "/economy/" + this.get("period") + "/instruction";
	},
	defaults: {
		entity_id: 0,
		instruction_number: 0,
		created_at: "",
		updated_at: "",
		accounting_date: "",
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