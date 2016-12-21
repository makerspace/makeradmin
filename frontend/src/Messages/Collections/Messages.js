import Backbone from 'backbone'
import Message from '../Models/Message'

module.exports = Backbone.PageableCollection.extend(
{
	model: Message,
	url: "/messages",
});