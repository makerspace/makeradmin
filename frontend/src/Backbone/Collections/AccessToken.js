import Backbone from 'backbone'
import AccessTokenModel from '../Models/AccessToken'

module.exports = Backbone.PageableCollection.extend(
{
	model: AccessTokenModel,
	url: "/oauth/token",
});