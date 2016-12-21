import Backbone from 'backbone'
import Recipient from '../Models/Recipient'

module.exports = Backbone.PageableCollection.extend(
{
	model: Recipient,
	url: function()
	{
		if(this.params.hasOwnProperty("member_id"))
		{
			return "/messages/user/" + this.params.member_id;
		}
		else
		{
			return "/messages/" + this.params.message_id + "/recipients";
		}
	}
});