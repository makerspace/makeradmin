import Backbone from 'backbone'
import AccountingPeriodModel from '../Models/AccountingPeriod'

var AccountingPeriodsCollection = Backbone.PageableCollection.extend(
{
	model: AccountingPeriodModel,
	url: "/economy/accountingperiod",
});

module.exports = AccountingPeriodsCollection;