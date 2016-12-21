import React from 'react'
import { withRouter } from 'react-router'
import TemplateForm from '../../Components/Forms/Template'

// Backbone
import TemplateModel from '../../Models/Template'

module.exports = withRouter(React.createClass({
	getInitialState: function()
	{
		return {
			model: new TemplateModel(),
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Skapa mall</h2>
				<TemplateForm model={this.state.model} route={this.props.route} />
			</div>
		);
	},
}));