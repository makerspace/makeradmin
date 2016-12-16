import Backbone from 'backbone'

var SubscriptionModel = Backbone.Model.fullExtend(
{
	idAttribute: "account_number",
	urlRoot: "/subscription",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		title: "",
		member_id: 0,
		product_id: 0,
		date_start: "0000-00-00T00:00:00Z",
	},
});

module.exports = SubscriptionModel;