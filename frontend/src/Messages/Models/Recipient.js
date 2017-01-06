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
		date_sent: "",
		status: 0,
	},
});