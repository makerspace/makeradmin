import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	url: function() {
		return "/member/current";
	},
	defaults: {
		created_at: "",
		updated_at: "",
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