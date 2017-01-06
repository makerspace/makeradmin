import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "entity_id",
	urlRoot: "/sales/product",
	defaults: {
		created_at: "",
		updated_at: "",
		title: "",
		description: "",
		expiry_date: "",
		price: 0,
		interval: "",
	},
});