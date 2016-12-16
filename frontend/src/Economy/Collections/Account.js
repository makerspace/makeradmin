import Backbone from 'backbone'
import AccountModel from '../Models/Account'
import config from '../../config'

var AccountCollection = Backbone.PageableCollection.extend(
{
	model: AccountModel,
	url: "/economy/" + config.accountingPeriod + "/account",
});

module.exports = AccountCollection;