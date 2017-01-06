import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "accountingperiod_id",
	urlRoot: "/economy/accountingperiod",
	defaults: {
		created_at: "",
		updated_at: "",
		title: "",
		description: "",
		name: "",
		start: "",
		end: "",
	},
});