import Backbone from 'backbone'
import CostCenterModel from '../Models/CostCenter'

module.exports = Backbone.PageableCollection.extend(
{
	model: CostCenterModel,
	// URL is always provided via the dataSource property in BackboneTable
});