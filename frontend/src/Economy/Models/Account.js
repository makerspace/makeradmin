import Backbone from 'backbone'
import config from '../../config'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "account_number",
	urlRoot: function()
	{
		return "/economy/" + this.get("period") + "/account";
	},
	defaults: {
		created_at: "",
		updated_at: "",
		account_number: "",
		title: "",
		description: "",
		balance: 0,
		accounting_transaction: [],
		instructions: [],
	},
});