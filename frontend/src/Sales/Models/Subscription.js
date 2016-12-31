import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "account_number",
	urlRoot: "/sales/subscription",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		title: "",
		product_id: 0,
		date_start: "0000-00-00T00:00:00Z",
	},
});