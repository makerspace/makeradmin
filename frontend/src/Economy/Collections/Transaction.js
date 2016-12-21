import Backbone from 'backbone'
import TransactionModel from '../Models/Transaction'
import config from '../../config'

var TransactionCollection = Backbone.PageableCollection.extend(
{
	model: TransactionModel,
	initialize: function(models, options)
	{
		this.id = options.id;
	},
	url: function(a)
	{
		return "/economy/" + this.params.period + "/account/" + this.params.account + "/transactions";
	},
});

module.exports = TransactionCollection;