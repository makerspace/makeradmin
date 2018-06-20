import Backbone from 'backbone'
import PermissionModel from '../Models/Permission'

module.exports = Backbone.PageableCollection.extend(
{
	model: PermissionModel,
	url: "/membership/permission",
});