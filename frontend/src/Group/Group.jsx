import React from 'react'
import BackboneReact from 'backbone-react-component'

// Backbone
import GroupModel from '../Backbone/Models/Group'
import MemberCollection from '../Backbone/Collections/Member'

import { Link, browserHistory } from 'react-router'
import GroupMembers from './Members'

var GroupHandler = React.createClass({
	getInitialState: function()
	{
		var group = new GroupModel({
			entity_id: this.props.params.id
		});
		group.fetch();

		this.title = "Meep";
		return {
			model: group,
		};
	},

	render: function()
	{
		return (
			<div>
				<Group model={this.state.model} />
				<GroupMembers type={MemberCollection}
					filters={{
						relations:
						[
							{
								entity_id: this.state.model.get("entity_id"),
							}
						]
					}}
				/>
			</div>
		);
	},
});
GroupHandler.title = "Visa grupp";

var GroupEditHandler = React.createClass({
	getInitialState: function()
	{
		var id = this.props.params.id;
		var group = new GroupModel({entity_id: id});
		group.fetch();

		this.title = "Meep";
		return {
			model: group,
		};
	},

	render: function()
	{
		return (
			<Group model={this.state.model} />
		);
	},
});
GroupEditHandler.title = "Visa grupp";

var GroupAddHandler = React.createClass({
	getInitialState: function()
	{
		var newGroup = new GroupModel();
		return {
			model: newGroup,
		};
	},

	render: function()
	{
		return (
			<div>
				<Group model={this.state.model} />
			</div>
		);
	},
});

var Group = React.createClass({
	mixins: [Backbone.React.Component.mixin],

	getInitialState: function()
	{
		return {
			error_column: "",
			error_message: "",
		};
	},

	cancel: function(event)
	{
		// Prevent the form from being submitted
		event.preventDefault();

		UIkit.modal.alert("TODO: Cancel");
	},

	remove: function(event)
	{
		// Prevent the form from being submitted
		event.preventDefault();

		UIkit.modal.alert("TODO: Remove");
	},

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
					browserHistory.push("/groups");
					UIkit.modal.alert("Successfully created");
				}
				else if(response.status == "updated")
				{
					browserHistory.push("/groups");
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

	error: function()
	{
		UIkit.modal.alert("Error saving model");
	},

	handleChange: function(event)
	{
		// Update the model with new value
		var target = event.target;
		var key = target.getAttribute("name");
		this.state.model[key] = target.value;

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
				<h2>{this.state.model.entity_id ? "Redigera grupp" : "Skapa grupp"}</h2>

				<form className="uk-form uk-form-horizontal" onSubmit={this.save}>
					<div className="uk-form-row">
						<label className="uk-form-label">Namn</label>
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
							<button className="uk-button uk-button-danger uk-float-left" onClick={this.cancel}><i className="uk-icon-close"></i> Avbryt</button>
							{this.state.model.entity_id ? <button className="uk-button uk-button-danger uk-float-left" onClick={this.remove}><i className="uk-icon-trash"></i> Ta bort grupp</button> : ""}
							<button className="uk-button uk-button-success uk-float-right" onClick={this.save}><i className="uk-icon-save"></i> Spara grupp</button>
						</div>
					</div>
				</form>
			</div>
		);
	},
});

module.exports = {
	GroupHandler,
	GroupAddHandler,
	GroupEditHandler,
	Group
}