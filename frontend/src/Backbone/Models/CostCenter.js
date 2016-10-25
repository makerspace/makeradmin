import Backbone from 'backbone'

var CostCenterModel = Backbone.Model.fullExtend(
{
	idAttribute: "account_number",
	urlRoot: "/economy/2015/costcenter",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		title: "",
		description: "",
	},
});

module.exports = CostCenterModel;