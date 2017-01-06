import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "entity_id",
	urlRoot: "/sales/history",
	defaults: {
		created_at: "",
		updated_at: "",
		recipient: "",
		title: "",
		description: "",
	},
});