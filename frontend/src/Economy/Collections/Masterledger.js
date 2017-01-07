import Backbone from 'backbone'
import AccountModel from '../Models/Account'

module.exports = Backbone.PageableCollection.extend(
{
	model: AccountModel,
	// URL is always provided via the dataSource property in BackboneTable
});