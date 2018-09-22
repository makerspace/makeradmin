import React from 'react';
import { withRouter } from 'react-router';
import Input2 from "../../Components/Form/Input2";
import Textarea2 from "../../Components/Form/Textarea2";
import {Async} from "react-select";
import { get } from "../../gateway";
import Group from "../../Models/Group";
import Member from "../../Models/Member";


// TODO Maybe not really a reusable component, check usages later (and move it to better place).


const groupOption = d => {
    const id = d[Group.model.id];
    const type = "group";
    return {
        id,
        type,
        label: `Grupp: ${d.title}`,
        value: type + id,
    };
};

const memberOption = d => {
    const id = d[Member.model.id];
    const type = "member";
    return {
        id,
        type,
        label: `Medlem: ${d.firstname} ${d.lastname} (#${d.member_number})`,
        value: type + id,
    };
};

class MessageForm extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            messageType: null,
            saveDisabled: true,
        };
    }
    
    componentDidMount() {
        const {message} = this.props;
        this.unsubscribe = message.subscribe(() => {
            this.setState({
                              sendDisabled: !message.canSave(),
                              message_type: message.message_type,
                              recipients: message.recipients,
                          });
        });
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    loadOptions(inputValue, callback) {
        Promise.all([
                        get({url: '/membership/group', params: {search: inputValue, sort_by: "name", sort_order: "asc"}}),
                        get({url: '/membership/member', params: {search: inputValue, sort_by: "firstname", sort_order: "asc"}}),
                    ])
               .then(([{data: groups}, {data: members}]) => callback(groups.map(d => groupOption(d)).concat(members.map(d => memberOption(d)))));
    }
    
    render() {
        
        
        const {message, onSave: onSend, recipientSelect} = this.props;
        const {sendDisabled, message_type, recipients} = this.state;
        
        return (
            <form className="uk-form uk-form-horizontal" onSubmit={(e) => {e.preventDefault(); onSend(); return false;}}>
                <div className="uk-form-row">
                    <label className="uk-form-label" htmlFor="message_type">
                        Typ
                    </label>
                    <div className="uk-form-controls">
                        <select id="message_type" ref="message_type" className="uk-form-width-medium" onChange={e => message.message_type =  e.target.value}>
                            <option value="email">E-post</option>
                            <option value="sms">SMS</option>
                        </select>
                    </div>
                </div>

                {
                    recipientSelect
                    ?
                    <div className="uk-form-row">
                        <label className="uk-form-label" htmlFor="recipient">
                            Mottagare
                        </label>
                        <div className="uk-form-controls">
                            <Async ref="recps"
                                   name="recipients"
                                   isMulti
                                   cache={false}
                                   placeholder="Type to search for member or group"
                                   getOptionValue={e => e.value}
                                   getOptionLabel={e => e.label}
                                   loadOptions={(v, c) => this.loadOptions(v, c)}
                                   value={recipients}
                                   onChange={values => message.recipients = values}
                            />
                        </div>
                    </div>
                    :
                    ""
                }

                {message_type === "email" ? <Input2 model={message} name="subject" title="Ärende"/> : ""}
                <Textarea2 model={message} name="body" title="Meddelande"/>

                <div className="uk-form-row">
                    <div className="uk-form-controls">
                        <p className="uk-float-left"><span id="characterCounter">{message.body.length}</span> tecken</p>
                    </div>
                    <div className="uk-form-controls">
                        <button className="uk-button uk-button-success uk-float-right" disabled={sendDisabled}><i className="uk-icon-save"/> Skicka</button>
                    </div>
                </div>
            </form>
        );
    }
}


export default withRouter(MessageForm);

// TODO Remove when fully fixed.

/*
module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, GenericEntityFunctions],

	getInitialState: function()
	{
		// Load template
		var _this = this;
		if(this.props.location.query.template !== undefined)
		{
			var template = new TemplateModel({template_id: this.props.location.query.template});
			template.fetch({success: function(data)
			{
				console.log("Done loading");
				_this.getModel().set({
					subject: data.get("title"),
					body: data.get("description"),
				});
			}});
		}

		var hideRecipientField = false;

		// The message_type attribute should not affect the isDirty() function on the model
		this.getModel().ignoreAttributes.push("message_type");

		// The form should have an hardcoded recipient
		if(this.props.recipient !== undefined)
		{
			// Save recipient in model
			var recipients = [];
			recipients.push(this.props.recipient);
			this.getModel().set("recipients", recipients);

			// A a hardcoded recipient list should not affect the isDirty() function on the model
			this.getModel().ignoreAttributes.push("recipients");

			// Hide form field from rendering
			hideRecipientField = true;
		}

		// Return default data
		return {
			recipients: [],
			hideRecipientField,
		};
	},

	onCreate: function(model)
	{
		this.setState({ignoreExitHook: true});
		this.props.router.push("/messages");
		UIkit.notify("Ditt meddelande har skickats", {status: "success"});
	},

	onSaveError: function()
	{
		UIkit.notify("Ett fel uppstod när meddelandet skulle skickas", {timeout: 0, status: "danger"});
	},

	onCancel: function(entity)
	{
		this.props.router.push("/messages");
	},

	// Change the between E-mail and SMS
	changeType: function()
	{
		// The subject should not affect the isDirty when the message type is set to SMS
		if(this.refs.message_type.value == "sms")
		{
			this.getModel().ignoreAttributes.push("subject");
		}
		else
		{
			var index = this.getModel().ignoreAttributes.indexOf("subject");
			if(index > -1)
			{
				this.getModel().ignoreAttributes.splice(index, 1);
			}
		}

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
			filteredRecipients.push(element.data);
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
		// Validate SMS
		if(
			this.state.model.message_type == "sms" &&
			this.state.model.recipients.length > 0 &&
			this.state.model.body.length > 0
		)
		{
			// Enable button
			return true;
		}
		// Validate E-mail
		else if(
			this.state.model.message_type == "email" &&
			this.state.model.recipients.length > 0 &&
			this.state.model.subject.length > 0 &&
			this.state.model.body.length > 0
		)
		{
			// Enable button
			return true;
		}

		// Disable button
		return false;
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

		// Use a Promise to concatenate the result from multiple AJAX requests
		var _this = this;
		$.when(
			this._executeSearch("member", input),
			this._executeSearch("group",  input),
		).then(function(members, groups)
		{
			// Get search result from server
			var members = _this._processResult("member", members[0].data);
			var groups  = _this._processResult("group",  groups[0].data);

			// Merge the result together and send to the auto complete callback
			var list = members.concat(groups);
			callback(list);
		});
	},

	// Send the AJAX request with the search query
	_executeSearch: function(type, input)
	{
		return $.ajax(
			{
				method: "GET",
				url: config.apiBasePath + "/membership/" + type,
				headers: {
					"Authorization": "Bearer " + auth.getAccessToken()
				},
				data: {
					search: input,
				},
			}
		);
	},

	// Process an array with search result from either groups or members and return a clean list
	_processResult: function(type, data)
	{
		var list = [];
		data.forEach(function(entity, index, array)
		{
			if(type == "member")
			{
				var id = entity.member_id;
				var title = "Medlem: " + entity.firstname + " " + entity.lastname + " (#" + entity.member_number + ")";
			}
			else
			{
				var id = entity.group_id;
				var title = "Grupp: " + entity.title;
			}

			list.push({
				label: title,
				value: type + id,
				data: {
					type: type,
					id: id,
				},
			});
		});

		return list;
	},

	// Called when the user is clicking an entity in the recipient list
	gotoMember: function(value, event)
	{
		if(value.data.type == "member")
		{
			UIkit.modal.alert("TODO: Visa medlem " + value.data.id);
		}
		else if(value.data.type == "group")
		{
			UIkit.modal.alert("TODO: Visa grupp " + value.data.id);
		}

		console.log(this.refs.recps);
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

				{this.state.hideRecipientField == false ?
					<div className="uk-form-row">
						<label className="uk-form-label" htmlFor="recipient">
							Mottagare
						</label>
						<div className="uk-form-controls">
							<Async ref="recps" isMulti cache={false} name="recipients" filterOption={this.filter} getOptionValue={e => e.value} getOptionLabel={e => e.label} loadOptions={this.search} value={this.state.recipients} onChange={this.changeRecipient} onValueClick={this.gotoMember} />
						</div>
					</div>
				: ""}

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
						<textarea id="body" ref="body" className="uk-form-width-large" rows="8" onChange={this.changeBody} value={this.state.model.body} />
					</div>
				</div>

				<div className="uk-form-row">
					<div className="uk-form-controls">
						<p className="uk-float-left"><span id="characterCounter">0</span> tecken</p>
					</div>
				</div>

				<div className="uk-form-row">
					<div className="uk-form-controls">
						{this.cancelButton()}
						{this.saveButton("Skicka")}
					</div>
				</div>
			</form>
		);
	},
}));

*/