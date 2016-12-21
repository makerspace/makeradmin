import React from 'react'
import BackboneReact from 'backbone-react-component'

import { Link, withRouter } from 'react-router'
import GenericEntityFunctions from '../../../GenericEntityFunctions'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, GenericEntityFunctions],

	getInitialState: function()
	{
		return {
			error_column: "",
			error_message: "",
		};
	},
	removeTextMessage: function(group)
	{
		return "Är du säker på att du vill ta bort gruppen \"" + group.title + "\"?";
	},

	removeErrorMessage: function()
	{
		UIkit.modal.alert("Fel uppstod vid borttagning av group");
	},

	removeSuccess: function(response)
	{
		UIkit.modal.alert("Successfully deleted");
		this.props.router.push("/groups");
	},

	createdSuccess: function(response)
	{
		UIkit.modal.alert("Successfully created");
		this.props.router.push("/groups/" + response.data.group_id);
	},

	updatedSuccess: function(response)
	{
		UIkit.modal.alert("Successfully updated");
	},

	saveError: function()
	{
		UIkit.modal.alert("Error saving model");
	},

/*
	save: function(event)
	{
		var _this = this;

		// Prevent the form from being submitted
		event.preventDefault();

		this.getModel().save([], {
			success: function(model, response)
			{
				if(response.status == "created")
				{
					this.props.router.push("/groups");
					UIkit.modal.alert("Successfully created");
				}
				else if(response.status == "updated")
				{
					this.props.router.push("/groups");
					UIkit.modal.alert("Successfully updated");
				}
				else
				{
					_this.error();
				}
			},
			error: function(model, xhr, options)
			{
				if(xhr.status == 422)
				{
					_this.setState({
						error_column:  xhr.responseJSON.column,
						error_message: xhr.responseJSON.message,
					});
				}
				else
				{

					_this.error();
				}
			},
		});
	},
*/

	handleChange: function(event)
	{
		// Update the model with new value
		var target = event.target;
		var key = target.getAttribute("name");
		this.getModel().set(key, target.value);

		// When we change the value of the model we have to rerender the component
		this.forceUpdate();
	},

	renderErrorMsg: function(column)
	{
		if(this.state.error_column == column)
		{
			return (
				<p className="uk-form-help-block error">Error: {this.state.error_message}</p>
			);
		}
	},

	render: function()
	{
		return (
			<div>
				<h2>{this.state.model.group_id ? "Redigera grupp" : "Skapa grupp"}</h2>

				<form className="uk-form uk-form-horizontal uk-margin-bottom" onSubmit={this.save}>
					<div className="uk-form-row">
						<label className="uk-form-label">Namn</label>
						<div className="uk-form-controls">
							<div className="uk-form-icon">
								<i className="uk-icon-tag"></i>
								<input type="text" name="name" className="uk-form-width-large" value={this.state.model.name} onChange={this.handleChange} />
							</div>
							{this.renderErrorMsg("name")}
						</div>
					</div>

					<div className="uk-form-row">
						<label className="uk-form-label">Titel</label>
						<div className="uk-form-controls">
							<div className="uk-form-icon">
								<i className="uk-icon-tag"></i>
								<input type="text" name="title" className="uk-form-width-large" value={this.state.model.title} onChange={this.handleChange} />
							</div>
							{this.renderErrorMsg("title")}
						</div>
					</div>

					<div className="uk-form-row">
						<label className="uk-form-label">Beskrivning</label>
						<div className="uk-form-controls">
							<textarea name="description" className="uk-form-width-large" value={this.state.model.description} onChange={this.handleChange}></textarea>
							{this.renderErrorMsg("description")}
						</div>
					</div>

					<div className="uk-form-row">
						<div className="uk-form-controls">
							<Link to="/groups" className="uk-button uk-button-danger uk-float-left"><i className="uk-icon-close"></i> Avbryt</Link>
							{this.state.model.group_id ? <button className="uk-button uk-button-danger uk-float-left" onClick={this.removeEntity}><i className="uk-icon-trash"></i> Ta bort grupp</button> : ""}
							<button className="uk-button uk-button-success uk-float-right" onClick={this.saveEntity}><i className="uk-icon-save"></i> Spara grupp</button>
						</div>
					</div>
				</form>
			</div>
		);
	},
}));