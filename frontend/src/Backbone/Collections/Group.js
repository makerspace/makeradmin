import Backbone from 'backbone'
import GroupModel from '../Models/Group'

var GroupCollection = Backbone.PageableCollection.extend(
{
	model: GroupModel,
	url: "/group",
});

module.exports = GroupCollection;