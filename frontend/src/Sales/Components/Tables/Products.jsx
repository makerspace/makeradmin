import React from 'react'
import BackboneReact from 'backbone-react-component'

import { Link } from 'react-router'
import BackboneTable from '../../../BackboneTable'
import Currency from '../../../Components/Currency'
import TableDropdownMenu from '../../../TableDropdownMenu'
import auth from '../../../auth'

module.exports = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 5,
		};
	},

	componentWillMount: function()
	{
		this.fetch();
	},

	componentDidMount: function(){
		var _this = this;
		$.ajax({
			method: "GET",
			url: config.apiBasePath + "/webshop/category",
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			},
		}).done(function(json) {
			const categories = new Map();
			json.data.forEach(function(element,index,array){
				categories.set(element.id, {action_id: element.id, name: element.name});
			});
			_this.setState({
				categories: categories,
			});
		});
	},

	removeTextMessage: function(entity)
	{
		return "Are you sure you want to remove product \"" + entity.title + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.notify("Error deleting product", {timeout: 0, status: "danger"});
	},

	renderHeader: function()
	{
		return [
			{
				title: "Namn",
				sort: "name",
			},
			{
				title: "Kategori",
				sort: "category_id",
			},
			{
				title: "Pris",
				sort: "price",
			},
			{
				title: "Enhet",
				sort: "unit",
			},
			{
				title: "",
			},
		];
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td><Link to={"/sales/product/" + row.id}>{row.name}</Link></td>
				<td>{this.state.categories ? this.state.categories.get(row.category_id).name : row.category_id}</td>
				<td className="uk-text-right"><Currency value={row.smallest_multiple*100*row.price} />kr</td>
				<td>{row.smallest_multiple == 1 ? row.unit : row.smallest_multiple + " " + row.unit}</td>
				<td>
					<TableDropdownMenu>
						<Link to={"/sales/product/" + row.id}><i className="uk-icon-cog" /> Redigera produkt</Link>
						{this.removeButton(i, "Ta bort produkt")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},
});
