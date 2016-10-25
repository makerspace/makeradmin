import Backbone from 'backbone'
import MemberModel from '../Models/Member'

var MemberCollection = Backbone.PageableCollection.extend(
{
	model: MemberModel,
	url: "/member",
});

module.exports = MemberCollection;