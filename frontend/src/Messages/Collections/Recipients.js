import Backbone from 'backbone'
import Recipient from '../Models/Recipient'

module.exports = Backbone.PageableCollection.extend(
{
	model: Recipient,
	// URL is always provided via the dataSource property in BackboneTable
});