import React from 'react'

// Backbone
import InstructionCollection from '../../Collections/Instruction'

import { Link, withRouter } from 'react-router'
import TableFilterBox from '../../../TableFilterBox'

import EconomyAccountingInstructions from '../../Components/Tables/Instructions'

module.exports = withRouter(React.createClass({
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
			<div className="uk-width-1-1">
				<h2>Verifikationer</h2>

				<p className="uk-float-left">Lista över samtliga verifikationer i bokföringen</p>
				<Link to={"/economy/" + this.props.params.period + "/instruction/add"} className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"></i> Skapa ny verifikation</Link>

				<TableFilterBox onChange={this.updateFilters} />

				<EconomyAccountingInstructions
					type={InstructionCollection}
					filters={this.state.filters}
					dataSource={{
						url: "/economy/" + this.props.params.period + "/instruction"
					}}
				/>
			</div>
		);
	}
}));
//EconomyAccountingInstructionsHandler.title = "Visa verifikationer";