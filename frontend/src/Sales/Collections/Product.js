import Backbone from 'backbone'
import ProductModel from '../Models/Product'

module.exports = Backbone.PageableCollection.extend(
{
	model: ProductModel,
	url: "/webshop/product",
});