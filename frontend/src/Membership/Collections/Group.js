import Backbone from 'backbone'
import GroupModel from '../Models/Group'

module.exports = Backbone.PageableCollection.extend(
{
	model: GroupModel,
	url: "/membership/group",
});