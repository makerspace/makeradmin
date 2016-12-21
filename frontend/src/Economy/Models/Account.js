import Backbone from 'backbone'
import config from '../../config'

var AccountModel = Backbone.Model.fullExtend(
{
	idAttribute: "account_number",
	urlRoot: function()
	{
		return "/economy/" + this.get("period") + "/account";
	},
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