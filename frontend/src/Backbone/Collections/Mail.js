import Backbone from 'backbone'
import MailModel from '../Models/Mail'

var MailCollection = Backbone.PageableCollection.extend(
{
	model: MailModel,
	url: "/messages",
});

module.exports = MailCollection;