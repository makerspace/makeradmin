import Backbone from 'backbone'
import AccountModel from '../Models/Account'
import config from '../../config'

var MasterledgerCollection = Backbone.PageableCollection.extend(
{
	model: AccountModel,
	url: "/economy/" + config.accountingPeriod + "/masterledger",
});

module.exports = MasterledgerCollection;