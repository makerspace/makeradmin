import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "permission_id",
	urlRoot: "/membership/permission",
	defaults: {
		permission: "",
	},
});