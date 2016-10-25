import React from 'react'

// Backbone
import RfidCollection from '../Backbone/Collections/Rfid'
import RfidModel from '../Backbone/Models/Rfid'

import Keys from './Keys'
import Edit from './Edit'

var KeysUserBox = React.createClass(
{
	getInitialState: function()
	{
		return {
			showEditForm: false,
		};
	},

	edit: function(model)
	{
		// Load the entity into the edit form
		this.setState({
			showEditForm: true,
			rfidModel: model,
		});
	},

	add: function()
	{
		var newRfid = new RfidModel();

		// Load the entity into the edit form
		this.setState({
			showEditForm: true,
			rfidModel: newRfid,
		});
	},

	rfidClose: function()
	{
		this.state.rfidModel.trigger("destroy", this.state.rfidModel);

		this.setState({
			showEditForm: false,
		});
	},

	rfidSave: function()
	{
		this.setState({
			showEditForm: false,
		});
	},

	render: function()
	{
		if(this.state.showEditForm)
		{
			return (
				<Edit model={this.state.rfidModel} ref="edit" member_number={this.props.member_number} close={this.rfidClose} save={this.rfidSave} />
			);
		}
		else
		{
			return (
				<div>
					<Keys type={RfidCollection}
						filters={{
							relations:
							[
								{
									type: "member",
									member_number: this.props.member_number,
								}
							]
						}}
					edit={this.edit} />
					<button className="uk-button uk-button-primary" onClick={this.add}><i className="uk-icon-plus-circle" /> Lägg till ny RFID-tagg</button>
				</div>
			);
		}
	},
});

module.exports = KeysUserBox