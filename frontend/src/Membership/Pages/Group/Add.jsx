import React from 'react'

// Backbone
import GroupModel from '../../Models/Group'

import Group from '../../Components/Forms/Group'
import { withRouter } from 'react-router'

module.exports = withRouter(React.createClass({
	getInitialState: function()
	{
		return {
			model: new GroupModel(),
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Skapa grupp</h2>
				<Group model={this.state.model} route={this.props.route} />
			</div>
		);
	},
}));