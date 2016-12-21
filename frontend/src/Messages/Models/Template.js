import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "template_id",
	urlRoot: "/messages/templates",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		name: "",
		title: "",
		description: "",
	},
});