import Backbone from 'backbone'
import CostCenterModel from '../Models/CostCenter'
import config from '../../config'

var CostCenterCollection = Backbone.PageableCollection.extend(
{
	model: CostCenterModel,
	url: function()
	{
		return "/economy/" + this.params.period + "/costcenter";
	},
});

module.exports = CostCenterCollection;