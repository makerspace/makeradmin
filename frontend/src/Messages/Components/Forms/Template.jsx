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

	removeErrorMessage: function()
	{
		UIkit.modal.alert("Fel uppstod vid borttagning av mall");
	},

	removeSuccess: function(response)
	{
		UIkit.modal.alert("Successfully deleted");
		this.props.router.push("/messages/templates");
	},

	createdSuccess: function(response)
	{
		UIkit.modal.alert("Successfully created");
		this.props.router.push("/messages/templates/" + response.data.template_id);
	},

	updatedSuccess: function(response)
	{
		UIkit.modal.alert("Successfully updated");
	},

	saveError: function()
	{
		UIkit.modal.alert("Error saving model");
	},

	handleChange: function(event)
	{
		// Update the model with new value
		var target = event.target;
		var key = target.getAttribute("name");
		this.getModel().set(key, target.value);

		// When we change the value of the model we have to rerender the component
		this.forceUpdate();
	},

	// Disable the send button if there is not enough data in the form
	enableSendButton: function()
	{
		// We need to have a delay so setState() has propely updated the state
		setTimeout(() =>
		{
			var disableSend = true;

			// Validate data
			if(
				this.state.model.name.length > 0 &&
				this.state.model.title.length > 0 &&
				this.state.model.description.length > 0
			)
			{
				disableSend = false;
			}

			// Update the status of the button
			this.setState({disableSend});
		}, 100);
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
					<Link className="uk-button uk-button-danger uk-float-left" to="/messages/templates"><i className="uk-icon-close"></i> Avbryt</Link>

					{this.state.model.template_id ? <button className="uk-button uk-button-danger uk-float-left" onClick={this.removeEntity}><i className="uk-icon-trash"></i> Radera mall</button> : ""}

					<button disabled={this.state.disableSend} onClick={this.saveEntity} className="uk-button uk-button-success uk-float-right"><i className="uk-icon-save"></i> Spara mall</button>
				</div>
			</form>
		);
	},
}));