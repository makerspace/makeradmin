import Backbone from 'backbone'
import SpanModel from '../Models/Span'

module.exports = Backbone.PageableCollection.extend(
{
	model: SpanModel,
	url: "/membership/span?expand=member",
});