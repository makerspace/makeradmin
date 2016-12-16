import React from 'react'

// Backbone
import MemberModel from '../../Models/Member'

import MemberForm from '../../MemberForm'

module.exports = React.createClass({
	getInitialState: function()
	{
		return {
			model: new MemberModel(),
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Skapa medlem</h2>
				<MemberForm model={this.state.model} />
			</div>
		);
	},
});
//MemberAddHandler.title = "Skapa medlem";