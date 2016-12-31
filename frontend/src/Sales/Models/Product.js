import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "entity_id",
	urlRoot: "/sales/product",
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