import React from 'react'
import { browserHistory } from 'react-router'
import { Async } from 'react-select';
import config from '../config'

/**
 * TODO:
 *   Validate data before sending
 */

class MailSendHandler extends React.Component
{
	constructor(props)
	{
		super(props);
		this.state = {
			type: "email",
			recipients: [],
			subject: "",
			body: "",
		};
	}

	// Change the between E-mail and SMS
	changeType()
	{
		this.setState({
			type: this.refs.type.value
		});
	}

	changeSubject()
	{
		this.setState({
			subject: this.refs.subject.value
		});
	}

	changeRecipient(value)
	{
		this.setState({
			recipients: value
		});

		// Clear the search history so there is no drop down with old data after adding a recipient
		this.refs.recps.setState({options: []});
	}

	changeBody()
	{
		this.setState({
			body: this.refs.body.value
		});

		// Update the character counter
		$("#characterCounter").html(this.refs.body.value.length);
	}

	// Disable client side filtering
	filter(option, filterString)
	{
		return option;
	}

	search(input, callback)
	{
		// Clear the search history so there is no drop down with old data when search text input is empty
		if(!input)
		{
			return Promise.resolve({ options: [] });
		}

		$.ajax({
			method: "GET",
			url: config.apiBasePath + "/member",
			data: {
				search: input,
			},
		}).done(function(data) {
			setTimeout(function() {
				var autoComplete = [];

				data.data.forEach(function(element, index, array){
					autoComplete.push({
						label: element.firstname + " " + element.lastname + " (#" + element.member_number + ")",
						value: element.member_number,
					});
				});

				callback(null, {
					options: autoComplete,
				});
			}, 100);
		});
	}

	gotoMember(value, event)
	{
		UIkit.modal.alert("TODO: Go to member " + value.label);
	}

	// Send an API request and queue the message to be sent
	send(event)
	{
		// Prevent the form from being submitted
		event.preventDefault();

		var type       = this.state.type;
		var recipients = this.state.recipients;
		var subject    = this.state.subject;
		var body       = this.state.body;

		// Send API request
		$.ajax({
			method: "POST",
			url: config.apiBasePath + "/mail",
			data: JSON.stringify({
				type,
				recipients,
				subject,
				body
			}),
		}).done(function (){
			// TODO: Falhantering
			browserHistory.push("/mail");
		});
	}

	cancel(event)
	{
		// Prevent the form from being submitted
		event.preventDefault();

		UIkit.modal.alert("TODO: Cancel");
	}

	render()
	{
		return (
			<div>
				<h2>Skapa utskick</h2>

				<form className="uk-form uk-form-horizontal" onSubmit={this.send.bind(this)}>
					<div className="uk-form-row">
						<label className="uk-form-label" htmlFor="type">
							Typ
						</label>
						<div className="uk-form-controls">
							<select id="type" ref="type" className="uk-form-width-medium" onChange={this.changeType.bind(this)}>
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
							<Async ref="recps" multi cache={false} name="recipients" filterOption={this.filter} loadOptions={this.search} value={this.state.recipients} onChange={this.changeRecipient.bind(this)} onValueClick={this.gotoMember} />
						</div>
					</div>

					{this.state.type == "email" ?
						<div className="uk-form-row">
							<label className="uk-form-label" htmlFor="subject">
								Ärende
							</label>
							<div className="uk-form-controls">
								<div className="uk-form-icon">
									<i className="uk-icon-commenting"></i>
									<input ref="subject" type="text" id="subject" name="subject" className="uk-form-width-large" onChange={this.changeSubject.bind(this)} />
								</div>
							</div>
						</div>
					: ""}

					<div className="uk-form-row">
						<label className="uk-form-label" htmlFor="body">
							Meddelande
						</label>

						<div className="uk-form-controls">
							<textarea id="body" ref="body" className="uk-form-width-large" rows="8" onChange={this.changeBody.bind(this)}></textarea>
						</div>
					</div>

					<div className="uk-form-row">
						<div className="uk-form-controls">
							<p className="uk-float-left"><span id="characterCounter">0</span> tecken</p>
						</div>
					</div>

					<div className="uk-form-row">
						<div className="uk-form-controls">
							<button className="uk-float-left uk-button uk-button-danger" onClick={this.cancel}><i className="uk-icon uk-icon-close" /> Avbryt</button>
							<button type="submit" className="uk-float-right uk-button uk-button-success"><i className="uk-icon uk-icon-envelope" /> Skicka</button>
						</div>
					</div>
				</form>
			</div>
		);
	}
}
MailSendHandler.title = "Skapa utskick";

module.exports = MailSendHandler