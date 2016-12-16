import Backbone from 'backbone'

var Message = Backbone.Model.fullExtend(
{
	idAttribute: "message_id",
	urlRoot: "/messages",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		type: "",
		recipients: 0,
		title: "",
		description: "",
		status: 0,
	},
});

module.exports = Message;