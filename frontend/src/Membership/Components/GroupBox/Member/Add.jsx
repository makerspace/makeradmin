import React from 'react'
import { Async } from 'react-select';
import { Link, withRouter } from 'react-router'
import auth from '../../../../auth'

module.exports = withRouter(React.createClass(
{
	getInitialState: function()
	{
		return {
			addMembers: "",
			disableSend: true,
		};
	},

	add: function()
	{
	},

	cancel: function()
	{
		this.setState({
			addMembers: "",
		});
	},

	changeValue: function(value)
	{
		this.setState({
			addMembers: value
		});

		var disabled = value.length == 0;
		this.setState({disableSend: disabled});

		// Clear the search history so there is no drop down with old data after adding a recipient
		this.refs.addmembers.setState({options: []});
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
			url: config.apiBasePath + "/membership/member",
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			},
			data: {
				search: input,
			},
		}).done(function(data) {
			setTimeout(function() {
				var autoComplete = [];

				data.data.forEach(function(element, index, array){
					autoComplete.push({
						label: "#"+element.member_number + ": " +element.firstname + " " + element.lastname,
						member_id: element.member_id,
					});
				});

				callback(autoComplete);
			}, 100);

		});
	},

	// Send an API request and queue the message to be sent
	save: function(event)
	{
		const _this = this;

		// Prevent the form from being submitted
		event.preventDefault();

		// Create a list of entity_id's that should relate to this entity
		const futures = [];
		this.state.addMembers.forEach(function(element, index, array) {
			// Send API request
			futures.push($.ajax({
				method: "POST",
				url: config.apiBasePath + "/membership/member/" + element.member_id + "/groups/add",
				headers: {
					"Authorization": "Bearer " + auth.getAccessToken()
				},
				data: JSON.stringify({
					groups: [_this.props.params.group_id],
				}),
				contentType: "application/json; charset=utf-8",
				dataType: "json",
			}));
		});
		Promise.all(futures).then(function () {
			_this.props.router.push("/membership/groups/" + _this.props.params.group_id + "/members");
		});
	},

	gotoMember: function(value, event)
	{
		UIkit.modal.alert("TODO: Show info for member " + value.label);
	},

	render: function()
	{
		return (
			<div>
				<form className="uk-form uk-form-horizontal" onSubmit={this.save}>
					<div className="uk-form-row">
						<label className="uk-form-label" htmlFor="members">
							Lägg till följande användare i gruppen
						</label>
						<div className="uk-form-controls">
							<Async ref="addmembers" isMulti cache={false} name="members" value={this.state.addMembers} filterOption={this.filter} getOptionValue={e => e.member_id} getOptionLabel={e => e.label} loadOptions={this.search} onChange={this.changeValue} onValueClick={this.gotoMember} />
						</div>
					</div>

					<div className="uk-form-row">
						<div className="uk-form-controls">
							<Link to={"/membership/groups/" + this.props.params.group_id + "/members"} className="uk-float-left uk-button uk-button-danger"><i className="uk-icon-close" /> Avbryt</Link>
							<button type="submit" disabled={this.state.disableSend} className="uk-float-right uk-button uk-button-success"><i className="uk-icon-save" /> Spara</button>
						</div>
					</div>
				</form>
			</div>
		);
	},
}));