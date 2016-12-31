import Backbone from 'backbone'
import AccountingPeriodModel from '../Models/AccountingPeriod'

module.exports = Backbone.PageableCollection.extend(
{
	model: AccountingPeriodModel,
	url: "/economy/accountingperiod",
});