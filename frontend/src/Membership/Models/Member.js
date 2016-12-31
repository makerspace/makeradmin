import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "member_id",
	urlRoot: "/membership/member",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		member_number: "",
		civicregno: "",
		firstname: "",
		lastname: "",
		email: "",
		phone: "",
		address_street: "",
		address_extra: "",
		address_zipcode: "",
		address_city: "",
		address_country: "se",
	},
});