import Backbone from 'backbone'

var GroupModel = Backbone.Model.fullExtend(
{
	idAttribute: "entity_id",
	urlRoot: "/group",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		title: "",
		description: "",
	},
});

module.exports = GroupModel;