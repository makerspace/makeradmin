import Backbone from 'backbone'

var RfidModel = Backbone.Model.fullExtend(
{
	idAttribute: "entity_id",
	urlRoot: "/rfid",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		tagid: "",
		description: "",
		status: "inactive",
		startdate: "0000-00-00T00:00:00Z",
		enddate: "0000-00-00T00:00:00Z",
	},
});

module.exports = RfidModel;