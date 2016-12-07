import Backbone from 'backbone'
import InvoiceModel from '../Models/Invoice'
import config from '../../config'

var InvoiceCollection = Backbone.PageableCollection.extend(
{
	model: InvoiceModel,
	url: "/economy/" + config.accountingPeriod + "/invoice",
});

module.exports = InvoiceCollection;