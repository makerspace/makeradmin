import React from 'react'
import BackboneReact from 'backbone-react-component'

import { Link, withRouter } from 'react-router'

import GenericEntityFunctions from '../../../GenericEntityFunctions'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, GenericEntityFunctions],

	removeTextMessage: function(template)
	{
		return "Är du säker på att du vill ta bort utskicksmallen \"" + template.title + "\"?";
	},

	onRemove: function(entity)
	{
		UIkit.notify("Successfully deleted", {status: "success"});
		this.props.router.push("/messages/templates");
	},

	onRemoveError: function()
	{
		UIkit.notify("Fel uppstod vid borttagning av mall", {timeout: 0, status: "danger"});
	},

	onCreate: function(model)
	{
		UIkit.notify("Successfully created", {status: "success"});
		this.props.router.push("/messages/templates/" + model.get("template_id"));
	},

	onUpdate: function(model)
	{
		UIkit.notify("Successfully updated", {status: "success"});
		this.props.router.push("/messages/templates");
	},

	onSaveError: function()
	{
		UIkit.notify("Error saving model", {timeout: 0, status: "danger"});
	},

	onCancel: function(entity)
	{
		this.props.router.push("/messages/templates");
	},

	// Disable the send button if there is not enough data in the form
	enableSendButton: function()
	{
		// Validate data
		if(
			this.getModel().isDirty() &&
			this.state.model.name.length > 0 &&
			this.state.model.title.length > 0 &&
			this.state.model.description.length > 0
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
			<form className="uk-form">
				<div className="uk-form-row">
					<label htmlFor="name" className="uk-form-label">{this.state.model.name ? "Namn" : ""}</label>
					<div className="uk-form-controls">
						<input type="text" name="name" id="name" value={this.state.model.name} placeholder="Namn" onChange={this.handleChange} className="uk-form-width-large" />
					</div>
				</div>

				<div className="uk-form-row">
					<label htmlFor="title" className="uk-form-label">{this.state.model.title ? "Titel" : ""}</label>
					<div className="uk-form-controls">
						<input type="text" name="title" id="title" value={this.state.model.title} placeholder="Titel" onChange={this.handleChange} className="uk-form-width-large" />
					</div>
				</div>

				<div className="uk-form-row">
					<label htmlFor="description" className="uk-form-label">{this.state.model.description ? "Meddelande" : ""}</label>
					<div className="uk-form-controls">
						<textarea name="description" onChange={this.handleChange} value={this.state.model.description} className="uk-form-width-large" rows="20"/>
					</div>
				</div>

				<div className="uk-form-row">
					{this.cancelButton()}
					{this.removeButton("Ta bort mall")}
					{this.saveButton("Spara mall")}
				</div>
			</form>
		);
	},
}));