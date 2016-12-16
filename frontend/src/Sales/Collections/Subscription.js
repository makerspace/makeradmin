import Backbone from 'backbone'
import SubscriptionModel from '../Models/Subscription'

var SubscriptionCollection = Backbone.PageableCollection.extend(
{
	model: SubscriptionModel,
	url: "/subscription",
});

module.exports = SubscriptionCollection;