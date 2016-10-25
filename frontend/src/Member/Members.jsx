import React from 'react'
import BackboneReact from 'backbone-react-component'

// Backbone
import MemberCollection from '../Backbone/Collections/Member'

import { Link } from 'react-router'
import BackboneTable from '../BackboneTable'
import DateField from '../Formatters/Date'
import config from '../config'
import TableDropdownMenu from '../TableDropdownMenu'
import TableFilterBox from '../TableFilterBox'

var MembersHandler = React.createClass({
	getInitialState: function()
	{
		return {
			filters: this.props.filters || {},
		};
	},

	updateFilters: function(newFilter)
	{
		var filters = this.overrideFiltersFromProps(newFilter);
		this.setState({
			filters: filters
		});
	},

	overrideFiltersFromProps: function(filters)
	{
		return filters;
	},

	render: function()
	{
		return (
			<div>
				<h2>Medlemmar</h2>

				<p className="uk-float-left">På denna sida ser du en lista på samtliga medlemmar.</p>
				<Link to="/members/add" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"></i> Skapa ny medlem</Link>

				<TableFilterBox onChange={this.updateFilters} />
				<Members type={MemberCollection} filters={this.state.filters} />
			</div>
		);
	},
});
MembersHandler.title = "Visa medlemmar";

var Members = React.createClass({
	mixins: [Backbone.React.Component.mixin, BackboneTable],

	getInitialState: function()
	{
		return {
			columns: 7,
		};
	},

/*
	// TODO: Få igång denna igen
	fetch: function(search)
	{
		if(search !== undefined && search.length > 0)
		{
			// Update the paginator so that is tells us we're on page 1
			this.pagination[1].currentPage = 0;
			this.pagination[2].currentPage = 0;
			this.pagination[1].render();
			this.pagination[2].render();

			// Make sure the Backbone collection will receive page 1
			this.getCollection().state.currentPage = 1;
		}
	},
*/
	componentWillMount: function()
	{
		this.fetch();
	},

	removeTextMessage: function(entity)
	{
		return "Are you sure you want to remove member \"" + entity.firstname + " " + entity.lastname + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.modal.alert("Error deleting member");
	},

	renderRow: function(row, i)
	{
		return (
			<tr key={i}>
				<td><Link to={"/members/" + row.member_number}>{row.member_number}</Link></td>
				<td>-</td>
				<td>{row.firstname}</td>
				<td>{row.lastname}</td>
				<td>{row.email}</td>
				<td><DateField date={row.created_at} /></td>
				<td>
					<TableDropdownMenu>
						<Link to={"/members/" + row.member_number}><i className="uk-icon uk-icon-cog"></i> Redigera medlem</Link>
						{this.removeButton(i, "Ta bort medlem")}
					</TableDropdownMenu>
				</td>
			</tr>
		);
	},

	renderHeader: function()
	{
		return [
			{
				title: "#",
				sort: "member_number",
			},
			{
				title: "Kön",
			},
			{
				title: "Förnamn",
				sort: "firstname",
			},
			{
				title: "Efternamn",
				sort: "lastname",
			},
			{
				title: "E-post",
				sort: "email",
			},
			{
				title: "Blev medlem",
				sort: "created_at",
			},
			{
				title: "",
			},
		];
	},
});

module.exports = {
	MembersHandler,
}