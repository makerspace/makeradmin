import Backbone from 'backbone'
import TransactionModel from '../Models/Transaction'
import config from '../../config'

module.exports = Backbone.PageableCollection.extend(
{
	model: TransactionModel,
	initialize: function(models, options)
	{
		this.id = options.id;
	},
	// URL is always provided via the dataSource property in BackboneTable
});