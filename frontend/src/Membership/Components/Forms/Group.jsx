import React from 'react'
import BackboneReact from 'backbone-react-component'

import { Link, withRouter } from 'react-router'
import GenericEntityFunctions from '../../../GenericEntityFunctions'

import Input from '../../../Components/Form/Input'
import Textarea from '../../../Components/Form/Textarea'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, GenericEntityFunctions],

	getInitialState: function()
	{
		return {
			error_column: "title",
			error_message: "meep meep",
		};
	},

	removeTextMessage: function(group)
	{
		return "Är du säker på att du vill ta bort gruppen \"" + group.title + "\"?";
	},

	onRemove: function(entity)
	{
		UIkit.notify("Successfully deleted", {status: "success"});
		this.props.router.push("/membership/groups");
	},

	onRemoveError: function()
	{
		UIkit.notify("Fel uppstod vid borttagning av group", {timeout: 0, status: "danger"});
	},

	onCreate: function(model)
	{
		UIkit.notify("Successfully created", {status: "success"});
		this.props.router.push("/membership/groups/" + model.get("group_id"));
	},

	onUpdate: function(model)
	{
		UIkit.notify("Successfully updated", {status: "success"});
		this.props.router.push("/membership/groups");
	},

	onSaveError: function()
	{
		UIkit.notify("Error saving model", {timeout: 0, status: "danger"});
	},

	onCancel: function(entity)
	{
		this.props.router.push("/membership/groups");
	},

	// Disable the send button if there is not enough data in the form
	enableSendButton: function()
	{
		// Validate required fields
		if(
			this.getModel().isDirty() &&
			this.state.model.name.length > 0 &&
			this.state.model.title.length > 0
		)
		{
			// Enable button
			return true;
		}

		// Disable button
		return false;
	},

	render: function()
	{
		return (
			<div className="meep">
				<form className="uk-form uk-margin-bottom" onSubmit={this.save}>
					<Input    model={this.getModel()} name="name"        title="Namn" />
					<Input    model={this.getModel()} name="title"       title="Titel" icon="tag" />
					<Textarea model={this.getModel()} name="description" title="Beskrivning" />

					<div className="uk-form-row uk-margin-top">
						<div className="uk-form-controls">
							{this.cancelButton()}
							{this.removeButton("Ta bort grupp")}
							{this.saveButton("Spara grupp")}
						</div>
					</div>
				</form>
			</div>
		);
	},
}));