import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "span_id",
	url: function() { return "/membership/span/" + this.get("span_id") + "?expand=member";},
	defaults: {
		span_type: "",
		startdate: null,
		enddate: null,
		member_number: "",
		firstname: "",
		lastname: "",
		created_at: "",
		updated_at: "",
	},
});