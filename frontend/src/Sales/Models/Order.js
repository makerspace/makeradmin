import Backbone from 'backbone'

module.exports = Backbone.Model.fullExtend(
{
	idAttribute: "id",
	urlRoot: "/webshop/transaction",
	defaults: {
		created_at: "",
		updated_at: "",
		member_id: "",
        status: "",
        amount: 0,
	},
});