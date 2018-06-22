import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "id",
	urlRoot: "/webshop/transaction_content",
	defaults: {
		transaction_id: "",
		product_id: "",
		count: "",
		amount: "",
		fulfillment: "",
	},
});