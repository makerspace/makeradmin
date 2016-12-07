import Backbone from 'backbone'

var AccountingPeriodModel = Backbone.Model.fullExtend(
{
	idAttribute: "accountingperiod_id",
	urlRoot: "/economy/accountingperiod",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		title: "",
		description: "",
		name: "",
		start: "0000-00-00T00:00:00Z",
		end: "0000-00-00T00:00:00Z",
	},
});

module.exports = AccountingPeriodModel;