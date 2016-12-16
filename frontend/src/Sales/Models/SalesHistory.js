import Backbone from 'backbone'

var SalesHistoryModel = Backbone.Model.fullExtend(
{
	idAttribute: "entity_id",
	urlRoot: "/sales/history",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		recipient: "",
		title: "",
		description: "",
	},
});

module.exports = SalesHistoryModel;