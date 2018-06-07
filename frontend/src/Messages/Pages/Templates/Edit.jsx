import React from 'react'

// Backbone
import TemplateModel from '../../Models/Template'

import TemplateForm from '../../Components/Forms/Template'
import { withRouter } from 'react-router'

module.exports = withRouter(React.createClass({
	getInitialState: function()
	{
		var model = new TemplateModel({
			template_id: this.props.params.id
		});

		var _this = this;
		model.fetch();

		return {
			model: model,
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Redigera mall</h2>
				<TemplateForm model={this.state.model} route={this.props.route} />
			</div>
		);
	},
}));