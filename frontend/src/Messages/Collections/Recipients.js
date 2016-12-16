import Backbone from 'backbone'
import Recipient from '../Models/Recipient'

var Recipients = Backbone.PageableCollection.extend(
{
	model: Recipient,
//	url: "/messages/1/recipients",// TODO
	url: function()
	{
		return "/messages/" + 123 + "/recipients";
	}
});

module.exports = Recipients;