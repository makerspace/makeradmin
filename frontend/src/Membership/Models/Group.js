import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "group_id",
	urlRoot: "/membership/group",
	defaults: {
		created_at: "",
		updated_at: "",
		parent: "",
		name: "",
		title: "",
		description: "",
	},
});