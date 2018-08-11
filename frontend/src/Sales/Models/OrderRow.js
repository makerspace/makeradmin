import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "id",
	urlRoot: "/webshop/transaction_content",
	defaults: {
		product_id: 0,
		product_name: "",
		count: 0,
		amount: 0,
		status: "",
	},
});