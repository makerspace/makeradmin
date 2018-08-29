import Backbone from 'backbone'
import KeyModel from '../Models/Key'

module.exports = Backbone.PageableCollection.extend(
{
	model: KeyModel,
	url: "/membership/key?expand=member",
});