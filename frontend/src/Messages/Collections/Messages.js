import Backbone from 'backbone'
import Message from '../Models/Message'

var Messages = Backbone.PageableCollection.extend(
{
	model: Message,
	url: "/messages",
});

module.exports = Messages;