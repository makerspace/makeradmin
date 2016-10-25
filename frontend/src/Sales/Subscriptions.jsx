import React from 'react'
import BackboneReact from 'backbone-react-component'

// Backbone
import SubscriptionCollection from '../Backbone/Collections/Subscription'
import SubscriptionModel from '../Backbone/Models/Subscription'

import { Link } from 'react-router'
import BackboneTable from '../BackboneTable'
import DateField from '../Formatters/Date'

var SalesSubscriptionsHandler = React.createClass({
	render: function()
	{
		return (
			<div>
				<h2>Prenumerationer</h2>
				<p>På denna sida ser du en lista på samtliga prenumerationer.</p>
				<Subscriptions type={SubscriptionCollection} />
			</div>
		);
	},
});
SalesSubscriptionsHandler.title = "Visa prenumerationer";

var Subscriptions = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 4,
		};
	},

	componentWillMount: function()
	{
		this.state.collection.fetch();
	},

	renderHeader: function ()
	{
		return [
			{
				title: "Member",
			},
			{
				title: "Startdatum",
			},
			{
				title: "Beskrivning",
			},
			{
				title: "Produkt",
			},
		];
	},

	renderRow: function (row, i)
	{
		return (
			<tr key={i}>
				<td>{row.member_id}</td>
				<td>{row.date_start}</td>
				<td>{row.title}</td>
				<td>{row.product_id}</td>
			</tr>
		);
	},
});

module.exports = {
	SalesSubscriptionsHandler
}