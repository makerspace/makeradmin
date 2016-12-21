import Backbone from 'backbone'
import config from '../../config'

var InvoiceModel = Backbone.Model.fullExtend(
{
	idAttribute: "invoice_number",
	urlRoot: function()
	{
		return "/economy/" + this.get("period") + "/invoice";
	},
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		invoice_number: 0,
		title: "",
		description: "",
		your_reference: "",
		our_reference: "",
		address: "",
		posts: [],
	},
});

module.exports = InvoiceModel;