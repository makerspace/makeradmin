import Backbone from 'backbone'
import CostCenterModel from '../Models/CostCenter'
import config from '../../config'

module.exports = Backbone.PageableCollection.extend(
{
	model: CostCenterModel,
	// URL is always provided via the dataSource property in BackboneTable
});