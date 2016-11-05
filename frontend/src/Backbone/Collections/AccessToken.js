import Backbone from 'backbone'
import AccessTokenModel from '../Models/AccessToken'

var AccessTokenCollection = Backbone.PageableCollection.extend(
{
	model: AccessTokenModel,
	url: "/oauth/token",
});

module.exports = AccessTokenCollection;