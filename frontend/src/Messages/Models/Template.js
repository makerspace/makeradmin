import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "template_id",
	urlRoot: "/messages/templates",
	defaults: {
		created_at: "",
		updated_at: "",
		name: "",
		title: "",
		description: "",
	},
});