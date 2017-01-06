import Backbone from 'backbone'
import config from '../../config'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "invoice_number",
	urlRoot: function()
	{
		return "/economy/" + this.get("period") + "/invoice";
	},
	defaults: {
		created_at: "",
		updated_at: "",
		invoice_number: 0,
		title: "",
		description: "",
		your_reference: "",
		our_reference: "",
		address: "",
		posts: [],
	},
});