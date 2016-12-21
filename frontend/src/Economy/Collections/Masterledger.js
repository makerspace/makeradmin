import Backbone from 'backbone'
import AccountModel from '../Models/Account'
import config from '../../config'

var MasterledgerCollection = Backbone.PageableCollection.extend(
{
	model: AccountModel,
	url: function()
	{
		return "/economy/" + this.params.period + "/masterledger";
	},
});

module.exports = MasterledgerCollection;