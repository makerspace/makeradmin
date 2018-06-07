import Backbone from 'backbone'
import SubscriptionModel from '../Models/Subscription'

module.exports = Backbone.PageableCollection.extend(
{
	model: SubscriptionModel,
	url: "/sales/subscription",
});