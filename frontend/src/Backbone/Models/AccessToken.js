import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "token_id",
	urlRoot: "/oauth/token",
	defaults: {
		expires: "",
		access_token: "",
		browser: "",
		ip: "",
	},
});