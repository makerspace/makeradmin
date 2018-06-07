import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "message_id",
	urlRoot: "/messages",
	defaults: {
		created_at: "",
		updated_at: "",
		subject: "",
		body: "",
		message_type: "email",
		status: "",
		recipients: [],
		num_recipients: 0,
	},
});