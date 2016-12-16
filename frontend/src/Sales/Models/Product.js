import Backbone from 'backbone'

var ProductModel = Backbone.Model.fullExtend(
{
	idAttribute: "entity_id",
	urlRoot: "/product",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		title: "",
		description: "",
		expiry_date: "",
		price: 0,
		interval: "",
	},
});

module.exports = ProductModel;