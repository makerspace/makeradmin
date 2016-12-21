import Backbone from 'backbone'
import AccountModel from '../Models/Account'
import config from '../../config'

var AccountCollection = Backbone.PageableCollection.extend(
{
	model: AccountModel,
	url: function()
	{
		return "/economy/" + this.params.period + "/account";
	},
});

module.exports = AccountCollection;