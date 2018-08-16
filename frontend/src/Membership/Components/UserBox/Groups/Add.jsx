import React from 'react'
import { Async } from 'react-select';
import { Link, withRouter } from 'react-router'
import auth from '../../../../auth'

module.exports = withRouter(React.createClass(
{
	getInitialState: function()
	{
		return {
			addGroups: "",
			disableSend: true,
		};
	},

	add: function()
	{
	},

	cancel: function()
	{
		this.setState({
			addGroups: "",
		});
	},

	changeValue: function(value)
	{
		this.setState({
			addGroups: value
		});

		var disabled = value.length == 0;
		this.setState({disableSend: disabled});

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
			url: config.apiBasePath + "/membership/group",
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			},
			data: {
				search: input,
			},
		}).done(function(data) {
			setTimeout(function() {
				callback(data.data);
			}, 100);

		});
	},

	// Send an API request and queue the message to be sent
	save: function(event)
	{
		var _this = this;

		// Prevent the form from being submitted
		event.preventDefault();

		// Create a list of entity_id's that should relate to this entity
		var groups = [];
		this.state.addGroups.forEach(function(element, index, array) {
			groups.push(element.group_id);
		});

		// Send API request
		$.ajax({
			method: "POST",
			url: config.apiBasePath + "/membership/member/" + this.props.params.member_id + "/groups/add",
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			},
			data: JSON.stringify({
				groups: groups,
			}),
			contentType: "application/json; charset=utf-8",
			dataType: "json",
		}).done(function () {
			_this.props.router.push("/membership/members/" + _this.props.params.member_id + "/groups");
		});
	},

	gotoGroup: function(value, event)
	{
		UIkit.modal.alert("TODO: Show info for group " + value.label);
	},

	render: function()
	{
		return (
			<div>
				<form className="uk-form uk-form-horizontal" onSubmit={this.save}>
					<div className="uk-form-row">
						<label className="uk-form-label" htmlFor="groups">
							Lägg till användaren i följande grupper
						</label>
						<div className="uk-form-controls">
							<Async ref="addgroups" isMulti cache={false} name="groups" value={this.state.addGroups} getOptionValue={e => e.group_id} getOptionLabel={e => e.title} filterOption={this.filter} loadOptions={this.search} onChange={this.changeValue} onValueClick={this.gotoGroup} />
						</div>
					</div>

					<div className="uk-form-row">
						<div className="uk-form-controls">
							<Link to={"/membership/members/" + this.props.params.member_id + "/groups"} className="uk-float-left uk-button uk-button-danger"><i className="uk-icon-close" /> Avbryt</Link>
							<button type="submit" disabled={this.state.disableSend} className="uk-float-right uk-button uk-button-success"><i className="uk-icon-save" /> Spara</button>
						</div>
					</div>
				</form>
			</div>
		);
	},
}));