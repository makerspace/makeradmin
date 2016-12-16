import Backbone from 'backbone'
import MemberModel from '../Models/Member'

var MemberCollection = Backbone.PageableCollection.extend(
{
	model: MemberModel,
	url: "/membership/member",
});

module.exports = MemberCollection;