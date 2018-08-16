import React from 'react'
import { Async } from 'react-select';
import { Link, withRouter } from 'react-router'
import auth from '../../../../auth'

module.exports = withRouter(React.createClass(
{
	getInitialState: function()
	{
		return {
			addPermissions: "",
			disableSend: true,
		};
	},

	add: function()
	{
	},

	cancel: function()
	{
		this.setState({
			addPermissions: "",
		});
	},

	changeValue: function(value)
	{
		this.setState({
			addPermissions: value
		});

		var disabled = value.length == 0;
		this.setState({disableSend: disabled});

		// Clear the search history so there is no drop down with old data after adding a recipient
		this.refs.addpermissions.setState({options: []});
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
			url: config.apiBasePath + "/membership/permission",
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
		var permissions = [];
		this.state.addPermissions.forEach(function(element, index, array) {
			permissions.push(element.permission_id);
		});

		// Send API request
		$.ajax({
			method: "POST",
			url: config.apiBasePath + "/membership/group/" + this.props.params.group_id + "/permissions/add",
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			},
			data: JSON.stringify({
				permissions: permissions,
			}),
			contentType: "application/json; charset=utf-8",
			dataType: "json",
		}).done(function () {
			_this.props.router.push("/membership/groups/" + _this.props.params.group_id + "/permissions");
		});
	},

	gotoPermission: function(value, event)
	{
		UIkit.modal.alert("TODO: Show info for permission " + value.label);
	},

	render: function()
	{
		return (
			<div>
				<form className="uk-form uk-form-horizontal" onSubmit={this.save}>
					<div className="uk-form-row">
						<label className="uk-form-label" htmlFor="permissions">
							Lägg följande behörigheter till grupp
						</label>
						<div className="uk-form-controls">
							<Async 
								ref="addpermissions"
								isMulti
								cache={false}
								name="permissions"
								value={this.state.addPermissions}
								getOptionValue={e => e.permission_id}
								getOptionLabel={e => e.permission}
								loadOptions={this.search}
								onChange={this.changeValue}
								onValueClick={this.gotoPermission} />
						</div>
					</div>

					<div className="uk-form-row">
						<div className="uk-form-controls">
							<Link to={"/membership/groups/" + this.props.params.group_id + "/permissions"} className="uk-float-left uk-button uk-button-danger"><i className="uk-icon-close" /> Avbryt</Link>
							<button type="submit" disabled={this.state.disableSend} className="uk-float-right uk-button uk-button-success"><i className="uk-icon-save" /> Spara</button>
						</div>
					</div>
				</form>
			</div>
		);
	},
}));