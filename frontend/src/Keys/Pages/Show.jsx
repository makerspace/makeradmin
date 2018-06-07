import React from 'react'

// Backbone
import KeyModel from '../Models/Key'

import Key from '../Components/Forms/Key'
import { withRouter } from 'react-router'

module.exports = withRouter(React.createClass({
	getInitialState: function()
	{
		var key = new KeyModel({
			key_id: this.props.params.id
		});

		key.fetch();

		return {
			model: key,
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Redigera RFID-tagg</h2>
				<Key model={this.state.model} route={this.props.route} />
			</div>
		);
	},
}));
//KeysOverviewHandler.title = "Nycklar";