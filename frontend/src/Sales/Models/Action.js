import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "id",
	urlRoot: "/webshop/product_action",
	defaults: {
		name: "",
	},
});