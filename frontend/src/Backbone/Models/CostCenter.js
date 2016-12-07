import Backbone from 'backbone'
import config from '../../config'

var CostCenterModel = Backbone.Model.fullExtend(
{
	idAttribute: "account_number",
	urlRoot: "/economy/" + config.accountingPeriod + "/costcenter",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		title: "",
		description: "",
	},
});

module.exports = CostCenterModel;