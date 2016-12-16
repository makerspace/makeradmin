import Backbone from 'backbone'
import CostCenterModel from '../Models/CostCenter'
import config from '../../config'

var CostCenterCollection = Backbone.PageableCollection.extend(
{
	model: CostCenterModel,
	url: "/economy/" + config.accountingPeriod + "/costcenter",
});

module.exports = CostCenterCollection;