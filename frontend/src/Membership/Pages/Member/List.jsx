import React from 'react'

// Backbone
import MemberCollection from '../../Collections/Member'

import { Link } from 'react-router'
import TableFilterBox from '../../../TableFilterBox'

import Members from '../../Members'

module.exports = React.createClass({
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
//MembersHandler.title = "Visa medlemmar";