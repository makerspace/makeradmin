import Backbone from 'backbone'
import RfidModel from '../Models/Rfid'

var RfidCollection = Backbone.PageableCollection.extend(
{
	model: RfidModel,
	url: "/rfid",
});

module.exports = RfidCollection;