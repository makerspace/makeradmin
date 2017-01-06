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
		created_at: "",
		updated_at: "",
		title: "",
		description: "",
	},
});