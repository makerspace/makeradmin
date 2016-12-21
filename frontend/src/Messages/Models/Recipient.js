import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "recipient_id",
	urlRoot: "/messages",
	defaults: {
		message_id: 0,
		title: "",
		description: "",
		member_id: 0,
		recipient: "",
		date_sent: "0000-00-00T00:00:00Z",
		status: 0,
	},
});