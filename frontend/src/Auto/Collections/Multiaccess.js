import Backbone from 'backbone'
import MultiaccessModel from '../Models/Multiaccess'

module.exports = Backbone.PageableCollection.extend(
{
	model: MultiaccessModel,
	url: "/multiaccess",
});