import Backbone from 'backbone'
import Template from '../Models/Template'

module.exports = Backbone.PageableCollection.extend(
{
	model: Template,
	url: "/messages/templates",
});