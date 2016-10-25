import Backbone from 'backbone'
import CostCenterModel from '../Models/CostCenter'

var CostCenterCollection = Backbone.PageableCollection.extend(
{
	model: CostCenterModel,
	url: "/economy/2015/costcenter",
});

module.exports = CostCenterCollection;