import Backbone from 'backbone'
import MemberModel from '../Models/Member'

module.exports = Backbone.PageableCollection.extend(
{
	model: MemberModel,
	url: "/membership/member",
});