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

	url: "/economy/" + config.accountingPeriod + "/transaction",
});

module.exports = TransactionCollection;