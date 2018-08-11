import Backbone from 'backbone';

export default Backbone.Model.fullExtend(
{
	idAttribute: "key_id",
	urlRoot: "/keys",
	defaults: {
		created_at: "",
		updated_at: "",
		title: "",
		description: "",
		tagid: "",
		status: "inactive",
		startdate: "",
		enddate: "",
	},
});
