import Backbone from 'backbone'
import ActionModel from '../Models/Action'

module.exports = Backbone.PageableCollection.extend(
{
	model: ActionModel,
	url: "/webshop/action",
});