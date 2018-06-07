import Backbone from 'backbone'
import SalesHistoryModel from '../Models/SalesHistory'

module.exports = Backbone.PageableCollection.extend(
{
	model: SalesHistoryModel,
	url: "/sales/history",
});