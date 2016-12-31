import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "token_id",
	urlRoot: "/oauth/token",
	defaults: {
		expires: "0000-00-00T00:00:00Z",
		access_token: "",
		browser: "",
		ip: "",
	},
});