import Backbone from 'backbone'

var TransactionModel = Backbone.Model.fullExtend(
{
	idAttribute: "entity_id",
	urlRoot: "/economy/2015/transaction",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		transaction_title: "",
		transaction_description: "",
		accounting_instruction: "",
		accounting_account: "",
		accounting_cost_center: "",
		amount: 0,
		external_id: "",
		instruction_title: "",
		instruction_number: 0,
		accounting_date: "0000-00-00T00:00:00Z",
		extid: 0,
		balance: 0,
	},
});

module.exports = TransactionModel;