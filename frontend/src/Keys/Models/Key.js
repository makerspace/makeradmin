import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "key_id",
	urlRoot: "/keys",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		title: "",
		description: "",
		tagid: "",
		status: "inactive",
		startdate: "0000-00-00T00:00:00Z",
		enddate: "0000-00-00T00:00:00Z",
		member_id: "",
	},
});