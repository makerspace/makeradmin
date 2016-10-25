import Backbone from 'backbone'
import AccountModel from '../Models/Account'

var AccountCollection = Backbone.PageableCollection.extend(
{
	model: AccountModel,
	url: "/economy/2015/account",
});

module.exports = AccountCollection;