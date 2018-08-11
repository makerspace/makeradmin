import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "id",
	urlRoot: "/webshop/product",
	defaults: {
		created_at: "",
		updated_at: "",
		name: "",
		description: "",
		category_id: "",
		price: 0,
		unit: "",
		smallest_multiple: 1,
	},
});