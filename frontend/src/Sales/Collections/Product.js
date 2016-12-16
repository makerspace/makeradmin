import Backbone from 'backbone'
import ProductModel from '../Models/Product'

var ProductCollection = Backbone.PageableCollection.extend(
{
	model: ProductModel,
	url: "/product",
});

module.exports = ProductCollection;