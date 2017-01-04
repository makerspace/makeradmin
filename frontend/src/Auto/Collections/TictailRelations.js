import Backbone from 'backbone'
import TictailRelationModel from '../Models/TictailRelation'

module.exports = Backbone.PageableCollection.extend(
{
	model: TictailRelationModel,
	url: "/auto/tictailrelations",
});