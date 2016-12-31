import Backbone from 'backbone'
import InvoiceModel from '../Models/Invoice'
import config from '../../config'

module.exports = Backbone.PageableCollection.extend(
{
	model: InvoiceModel,
	// URL is always provided via the dataSource property in BackboneTable
});