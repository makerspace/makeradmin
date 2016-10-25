import Backbone from 'backbone'

var MemberModel = Backbone.Model.fullExtend(
{
	idAttribute: "member_number",
	urlRoot: "/member",
	defaults: {
		created_at: "0000-00-00T00:00:00Z",
		updated_at: "0000-00-00T00:00:00Z",
		entity_id: 0,
		member_number: null,
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

module.exports = MemberModel;