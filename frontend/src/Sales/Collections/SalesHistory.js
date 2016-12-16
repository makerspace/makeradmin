import Backbone from 'backbone'
import SalesHistoryModel from '../Models/SalesHistory'

var SalesHistoryCollection = Backbone.PageableCollection.extend(
{
	model: SalesHistoryModel,
	url: "/sales/history",
});

module.exports = SalesHistoryCollection;