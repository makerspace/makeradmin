import React from 'react'
import { Groups } from './Groups'

// Backbone
import GroupCollection from '../Backbone/Collections/Group'

import { Async } from 'react-select';
import config from '../config'

var GroupUserBox = React.createClass(
{
	getInitialState: function()
	{
		return {
			showEditForm: false,
			addGroups: "",
		};
	},

	add: function()
	{
		this.setState({
			showEditForm: true,
		});
	},

	cancel: function()
	{
		this.setState({
			showEditForm: false,
			addGroups: "",
		});
	},

	changeValue: function(value)
	{
		this.setState({
			addGroups: value
		});

		// Clear the search history so there is no drop down with old data after adding a recipient
		this.refs.addgroups.setState({options: []});
	},

	// Disable client side filtering
	filter: function(option, filterString)
	{
		return option;
	},

	search: function(input, callback)
	{
		// Clear the search history so there is no drop down with old data when search text input is empty
		if(!input)
		{
			return Promise.resolve({ options: [] });
		}

		$.ajax({
			method: "GET",
			url: config.apiBasePath + "/group",
			data: {
				search: input,
			},
		}).done(function(data) {
			setTimeout(function() {
				var autoComplete = [];

				data.data.forEach(function(element, index, array){
					autoComplete.push({
						label: element.title + ": " + element.description,
						value: element.entity_id,
					});
				});

				callback(null, {
					options: autoComplete,
				});
			}, 100);

		});
	},

	// Send an API request and queue the message to be sent
	send: function(event)
	{
		var _this = this;

		// Prevent the form from being submitted
		event.preventDefault();

		// Create a list of entity_id's that should relate to this entity
		var entity2 = [];
		this.state.addGroups.forEach(function(element, index, array) {
			entity2.push(element.value);
		});

		// Send API request
		$.ajax({
			method: "POST",
			url: config.apiBasePath + "/relation",
			data: JSON.stringify({
				entity1: [{
					relations:
						[
							{
								type: "member",
								member_number: this.props.member_number,
							}
						],
					}],
				entity2: entity2,
			}),
		}).done(function (){
/*
			_this.setState({
				showEditForm: false,
				addGroups: "",
			});
*/
		});
	},

	gotoGroup: function(value, event)
	{
		UIkit.modal.alert("TODO: Go to member " + value.label);
	},

	render: function()
	{
		if(this.state.showEditForm)
		{
			return (
				<div>
					<form className="uk-form uk-form-horizontal" onSubmit={this.send}>
						<div className="uk-form-row">
							<label className="uk-form-label" htmlFor="groups">
								Lägg till användaren i följande grupper
							</label>
							<div className="uk-form-controls">
								<Async ref="addgroups" multi cache={false} name="groups" value={this.state.addGroups} filterOption={this.filter} loadOptions={this.search} onChange={this.changeValue} onValueClick={this.gotoGroup} />
							</div>
						</div>

						<div className="uk-form-row">
							<div className="uk-form-controls">
								<button className="uk-float-left uk-button uk-button-danger" onClick={this.cancel}><i className="uk-icon-close" /> Avbryt</button>
								<button className="uk-float-right uk-button uk-button-success" onClick={this.save}><i className="uk-icon-save" /> Spara</button>
							</div>
						</div>

					</form>
				</div>
			);
		}
		else
		{
			return (
				<div>
					<Groups type={GroupCollection}
						filters={{
							relations:
							[
								{
									type: "member",
									member_number: this.props.member_number,
								}
							]
						}}
					/>
					<button className="uk-button uk-button-primary" onClick={this.add}><i className="uk-icon-plus-circle" /> Lägg till grupp</button>
				</div>
			);
		}
	},
});

module.exports = GroupUserBox