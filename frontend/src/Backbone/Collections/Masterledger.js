import Backbone from 'backbone'
import AccountModel from '../Models/Account'

var MasterledgerCollection = Backbone.PageableCollection.extend(
{
	model: AccountModel,
	url: "/economy/2015/masterledger",
});

module.exports = MasterledgerCollection;