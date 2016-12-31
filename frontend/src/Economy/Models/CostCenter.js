import Backbone from 'backbone'
import config from '../../config'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "account_number",
	urlRoot: function()
	{
		return "/economy/" + this.get("period") + "/costcenter";
	},
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		title: "",
		description: "",
	},
});