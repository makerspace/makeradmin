import Backbone from 'backbone'
import InvoiceModel from '../Models/Invoice'
import config from '../../config'

var InvoiceCollection = Backbone.PageableCollection.extend(
{
	model: InvoiceModel,
	url: function()
	{
		return "/economy/" + this.params.period + "/invoice";
	},
});

module.exports = InvoiceCollection;