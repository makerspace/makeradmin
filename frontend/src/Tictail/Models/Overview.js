import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "entity_id",
	urlRoot: "/sales/product",
	defaults: {
		tictail: "",
		storage: "",
		instruction: "",
	},
});