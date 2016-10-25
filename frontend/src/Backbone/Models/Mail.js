import Backbone from 'backbone'

var MailModel = Backbone.Model.fullExtend(
{
	idAttribute: "entity_id",
	urlRoot: "/mail",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		type: "",
		recipient: "",
		title: "",
		description: "",
		status: 0,
		date_sent: "0000-00-00T00:00:00Z",
	},
});

module.exports = MailModel;