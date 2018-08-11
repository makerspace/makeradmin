import Backbone from 'backbone'
import OrderModel from '../Models/Order'

module.exports = Backbone.PageableCollection.extend(
{
	model: OrderModel,
	url: "/webshop/transactions_extended_info",
});
