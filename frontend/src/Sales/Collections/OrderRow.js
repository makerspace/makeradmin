import Backbone from 'backbone'
import OrderRowModel from '../Models/OrderRow'

module.exports = Backbone.PageableCollection.extend(
{
	model: OrderRowModel,
	url: "/webshop/transaction_content",
});