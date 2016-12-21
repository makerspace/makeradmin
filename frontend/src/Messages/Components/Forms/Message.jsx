import React from 'react'
import config from '../../../config'
import { Link, withRouter } from 'react-router'
import { Async } from 'react-select';
import GenericEntityFunctions from '../../../GenericEntityFunctions'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, GenericEntityFunctions],

	getInitialState: function()
	{
		return {
			recipients: [],
		};
	},

	createdSuccess: function(response)
	{
		this.setState({ignoreExitHook: true});
		this.props.router.push("/messages");
	},

	saveError: function()
	{
		UIkit.modal.alert("Ett fel uppstod när meddelandet skulle skickas");
	},

	// Change the between E-mail and SMS
	changeType: function()
	{
		this.getModel().set("message_type", this.refs.message_type.value);
	},

	// Change recipients
	changeRecipient: function(value)
	{
		// Keep a separate list of recipients so the auto complete plugin get it's own format
		this.setState({recipients: value});

		// Filter recipients (Remove label)
		var filteredRecipients = [];
		value.forEach(function(element, index, array) {
			filteredRecipients.push(element.value);
		});

		// Update the model with the filtered recipient list
		this.getModel().set("recipients", filteredRecipients);

		// Clear the search history so there is no drop down with old data after adding a recipient
		this.refs.recps.setState({options: []});
	},

	// Change the subject
	changeSubject: function()
	{
		this.getModel().set("subject", this.refs.subject.value);
	},

	// Change message body
	changeBody: function()
	{
		this.getModel().set("body", this.refs.body.value);

		// Update the character counter
		$("#characterCounter").html(this.refs.body.value.length);
	},

	// Disable the send button if there is not enough data in the form
	enableSendButton: function()
	{
		// We need to have a delay so setState() has propely updated the state
		setTimeout(() =>
		{
			var disableSend = true;

			// Validate SMS
			if(
				this.state.model.message_type == "sms" &&
				this.state.model.recipients.length > 0 &&
				this.state.model.body.length > 0
			)
			{
				disableSend = false;
			}
			// Validate E-mail
			else if(
				this.state.model.message_type == "email" &&
				this.state.model.recipients.length > 0 &&
				this.state.model.subject.length > 0 &&
				this.state.model.body.length > 0
			)
			{
				disableSend = false;
			}

			// Update the status of the button
			this.setState({disableSend});
		}, 100);
	},

	// Disable client side filtering
	filter: function(option, filterString)
	{
		return option;
	},

	// Called when the user is typing anything in the recipient input
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
			data: {
				search: input,
			},
		}).done(function(data) {
			setTimeout(function() {
				var autoComplete = [];

				data.data.forEach(function(element, index, array){
					autoComplete.push({
						label: "Member:" + element.firstname + " " + element.lastname + " (#" + element.member_number + ")",
						value: {
							type: "member",
							id: element.member_id,
						},
					});
				});

				callback(null, {
					options: autoComplete,
				});
			}, 100);
		});
	},

	// Called when the user is clicking a member in the recipient list
	gotoMember: function(value, event)
	{
		UIkit.modal.alert("TODO: Go to member " + value.label);
	},

	// Render the page
	render: function()
	{
		return (
			<form className="uk-form uk-form-horizontal">
				<div className="uk-form-row">
					<label className="uk-form-label" htmlFor="message_type">
						Typ
					</label>
					<div className="uk-form-controls">
						<select id="message_type" ref="message_type" className="uk-form-width-medium" onChange={this.changeType}>
							<option value="email">E-post</option>
							<option value="sms">SMS</option>
						</select>
					</div>
				</div>

				<div className="uk-form-row">
					<label className="uk-form-label" htmlFor="recipient">
						Mottagare
					</label>
					<div className="uk-form-controls">
						<Async ref="recps" multi cache={false} name="recipients" filterOption={this.filter} loadOptions={this.search} value={this.state.recipients} onChange={this.changeRecipient} onValueClick={this.gotoMember} />
					</div>
				</div>

				{this.state.model.message_type == "email" ?
					<div className="uk-form-row">
						<label className="uk-form-label" htmlFor="subject">
							Ärende
						</label>
						<div className="uk-form-controls">
							<div className="uk-form-icon">
								<i className="uk-icon-commenting"></i>
								<input ref="subject" type="text" id="subject" name="subject" className="uk-form-width-large" onChange={this.changeSubject} value={this.state.model.subject} />
							</div>
						</div>
					</div>
				: ""}

				<div className="uk-form-row">
					<label className="uk-form-label" htmlFor="body">
						Meddelande
					</label>

					<div className="uk-form-controls">
						<textarea id="body" ref="body" className="uk-form-width-large" rows="8" onChange={this.changeBody}></textarea>
					</div>
				</div>

				<div className="uk-form-row">
					<div className="uk-form-controls">
						<p className="uk-float-left"><span id="characterCounter">0</span> tecken</p>
					</div>
				</div>

				<div className="uk-form-row">
					<div className="uk-form-controls">
						<Link className="uk-float-left uk-button uk-button-danger" to="/messages"><i className="uk-icon-close" /> Avbryt</Link>
						<button disabled={this.state.disableSend} onClick={this.saveEntity} className="uk-float-right uk-button uk-button-success"><i className="uk-icon-envelope" /> Skicka</button>
					</div>
				</div>
			</form>
		);
	},
}));