import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "message_id",
	urlRoot: "/messages",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		subject: "",
		body: "",
		message_type: "email",
		status: "",
		recipients: [],
		num_recipients: 0,
	},
});