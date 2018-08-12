import Backbone from 'backbone';

export default Backbone.Model.fullExtend(
{
	idAttribute: "key_id",
	urlRoot: "/membership/key",
	defaults: {
		member_id: "",
		created_at: "",
		updated_at: "",
		description: "",
		tagid: "",
		startdate: "",
		enddate: "",
	},
});
