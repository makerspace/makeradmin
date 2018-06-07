import Backbone from 'backbone'
import OverviewModel from '../Models/Overview'

module.exports = Backbone.PageableCollection.extend(
{
	model: OverviewModel,
	url: "/tictail/overview",
});