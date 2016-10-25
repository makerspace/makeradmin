import Backbone from 'backbone'

var AccountModel = Backbone.Model.fullExtend(
{
	idAttribute: "account_number",
	urlRoot: "/economy/2015/account",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		account_number: "",
		title: "",
		description: "",
		balance: 0,
		accounting_transaction: [],
		instructions: [],
	},
});

module.exports = AccountModel;