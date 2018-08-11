import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "id",
	defaults: {
		content_id: "",
		action: "",
		value: "",
		status: "",
	},
});