import React from 'react'
import BackboneReact from 'backbone-react-component'

// Backbone
import MemberModel from '../Backbone/Models/Member'

import { Link, browserHistory } from 'react-router'
import DateField from '../Formatters/Date'

// Import functions from other modules
import KeysUserBox from '../Keys/KeysUserBox'
import MailUserBox from '../Mail/MailUserBox'
import GroupUserBox from '../Group/GroupUserBox'
import SubscriptionUserBox from '../Sales/SubscriptionUserBox'
import TransactionUserBox from '../Economy/TransactionUserBox'

import CountryDropdown from '../CountryDropdown'
import DateTimeField from '../Formatters/DateTime'

var MemberHandler = React.createClass({
	getInitialState: function()
	{
		var member = new MemberModel({
			member_number: this.props.params.id
		});

		var _this = this;
		member.fetch({
			success: function() {
				// This component does not use the ReactBackbone mixin, so we have to force redraw it when the Backbone model is loaded from the server
				_this.forceUpdate();
			}
		});

//		this.title = "Meep";
		return {
			model: member,
		};
	},

	componentDidMount: function()
	{
		// Ugly way to get the switcher javascript working
		$.UIkit.init();
/*
		var _this = this;
		$("[data-uk-switcher]").on("show.uk.switcher", function(event, area) {
			if(area.context.id == "member_keys")
			{
				if(!this.keys_synced)
				{
					// Get the RFID keys associated with the member
					_this.state.model.keys = 
					_this.state.collection = _this.state.model.keys;

					_this.state.model.keys.fetch();
					this.keys_synced = true;
				}
			}
		});
*/
	},

	render: function()
	{
		return (
			<div>
				<h2>Medlem #{this.state.model.get("member_number")}: {this.state.model.get("firstname")} {this.state.model.get("lastname")}</h2>

				<ul className="uk-tab" data-uk-switcher="{connect:'#user-tabs'}">
					<li id="member_info"><a>Personuppgifter</a></li>
					<li id="member_groups"><a>Grupper</a></li>
					<li id="member_keys"><a>Nycklar</a></li>
					<li id="member_labaccess"><a>Prenumerationer</a></li>
					<li id="member_transactions"><a>Transaktioner</a></li>
					<li id="member_groups"><a>Utskick</a></li>
				</ul>

				<ul id="user-tabs" className="uk-switcher">
					<li>
						<MemberForm model={this.state.model} />
					</li>
					<li>
						<GroupUserBox member_number={this.state.model.get("member_number")} />
					</li>
					<li>
						<KeysUserBox member_number={this.state.model.get("member_number")} />
					</li>
					<li>
						<SubscriptionUserBox member_number={this.state.model.get("member_number")} />
					</li>
					<li>
						<TransactionUserBox member_number={this.state.model.get("member_number")} />
					</li>
					<li>
						<MailUserBox member_number={this.state.model.get("member_number")} />
					</li>
				</ul>
			</div>
		);
	},
});
MemberHandler.title = "Visa medlem";

var MemberForm = React.createClass({
	mixins: [Backbone.React.Component.mixin],

	cancel: function(event)
	{
		// Prevent the form from being submitted
		event.preventDefault();

		UIkit.modal.alert("TODO: Clear form");
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
					UIkit.modal.alert("Successfully created");
					browserHistory.push("/members/" + response.entity.member_number);
				}
				else if(response.status == "updated")
				{
					UIkit.modal.alert("Successfully updated");
				}
				else
				{
					_this.error();
				}
			},
			error: function(model, response, options) {
				_this.error();
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

	render: function()
	{
		return (
			<div className="meep">
			<form className="uk-form">
				<fieldset >
					<legend><i className="uk-icon-user"></i> Personuppgifter</legend>

					<div className="uk-form-row">
						<label htmlFor="civicregno" className="uk-form-label">{this.state.model.civicregno ? "Personnummer" : ""}</label>
						<div className="uk-form-controls">
							<input type="text" name="civicregno" id="civicregno" value={this.state.model.civicregno} placeholder="Personnummer" onChange={this.handleChange} className="uk-form-width-large" />
						</div>
					</div>

					<div className="uk-form-row">
						<label htmlFor="firstname" className="uk-form-label">{this.state.model.firstname ? "Förnamn" : ""}</label>
						<div className="uk-form-controls">
							<input type="text" name="firstname" id="firstname" value={this.state.model.firstname} placeholder="Förnamn" onChange={this.handleChange} className="uk-form-width-large" />
						</div>
					</div>

					<div className="uk-form-row">
						<label htmlFor="lastname" className="uk-form-label">{this.state.model.lastname ? "Efternamn" : ""}</label>
						<div className="uk-form-controls">
							<input type="text" name="lastname" id="lastname" value={this.state.model.lastname} placeholder="Efternamn" onChange={this.handleChange} className="uk-form-width-large" />
						</div>
					</div>

					<div className="uk-form-row">
						<label htmlFor="email" className="uk-form-label">{this.state.model.email ? "E-post" : ""}</label>
						<div className="uk-form-controls">
							<div className="uk-form-icon">
								<i className="uk-icon-envelope"></i>
								<input type="text" name="email" id="email" value={this.state.model.email} placeholder="E-postadress" onChange={this.handleChange} className="uk-form-width-large" />
							</div>
						</div>
					</div>

					<div className="uk-form-row">
						<label htmlFor="phone" className="uk-form-label">{this.state.model.phone ? "Telefonnummer" : ""}</label>
						<div className="uk-form-controls">
							<div className="uk-form-icon">
								<i className="uk-icon-phone"></i>
								<input type="text" name="phone" id="phone" value={this.state.model.phone} placeholder="Telefonnummer" onChange={this.handleChange} className="uk-form-width-large" />
							</div>
						</div>
					</div>
				</fieldset>

				<fieldset data-uk-margin>
					<legend><i className="uk-icon-home"></i> Adress</legend>

					<div className="uk-form-row">
						<label htmlFor="address_street" className="uk-form-label">{this.state.model.address_street ? "Address" : ""}</label>
						<div className="uk-form-controls">
							<input type="text" name="address_street" id="address_street" value={this.state.model.address_street} placeholder="Adress inkl gatunummer och lägenhetsnummer" onChange={this.handleChange} className="uk-form-width-large" />
						</div>
					</div>

					<div className="uk-form-row">
						<label htmlFor="address_extra" className="uk-form-label">{this.state.model.address_extra ? "Address extra" : ""}</label>
						<div className="uk-form-controls">
							<input type="text" name="address_extra" id="address_extra" value={this.state.model.address_extra} placeholder="Extra adressrad, t ex C/O adress" onChange={this.handleChange} className="uk-form-width-large" />
						</div>
					</div>

					<div className="uk-form-row">
						<div className="zipcode">
							<label htmlFor="address_zipcode" className="uk-form-label">{this.state.model.address_zipcode ? "Postnummer" : ""}</label>
							<div className="uk-form-controls">
								<input type="text" name="address_zipcode" id="address_zipcode" value={this.state.model.address_zipcode} placeholder="Postnummer" onChange={this.handleChange} className="uk-form-width-small" />
							</div>
						</div>

						<div className="city">
							<label htmlFor="address_city" className="uk-form-label">{this.state.model.address_city ? "Postort" : ""}</label>
							<div className="uk-form-controls">
								<input type="text" name="address_city" id="address_city" value={this.state.model.address_city} placeholder="Postort" onChange={this.handleChange} />
							</div>
						</div>
					</div>

					<div className="uk-form-row">
						<label htmlFor="" className="uk-form-label">Land</label>
						<div className="uk-form-controls">
							<CountryDropdown country={this.state.model.address_country} onChange={this.changeCountry} />
						</div>
					</div>
				</fieldset>

				{this.state.model.entity_id > 0 ?
					<fieldset data-uk-margin>
						<legend><i className="uk-icon-tag"></i> Metadata</legend>

						<div className="uk-form-row">
							<label className="uk-form-label">Medlem sedan</label>
							<div className="uk-form-controls">
								<i className="uk-icon-calendar"></i>
								&nbsp;
								<DateTimeField date={this.state.model.created_at} />
							</div>
						</div>

						<div className="uk-form-row">
							<label className="uk-form-label">Senast uppdaterad</label>
							<div className="uk-form-controls">
								<i className="uk-icon-calendar"></i>
								&nbsp;
								<DateTimeField date={this.state.model.updated_at} />
							</div>
						</div>
					</fieldset>
				: ""}

				<div className="uk-form-row">
					<button className="uk-button uk-button-danger uk-float-left" onClick={this.cancel}><i className="uk-icon-close"></i> Avbryt</button>

					{this.state.model.entity_id ? <button className="uk-button uk-button-danger uk-float-left" onClick={this.remove}><i className="uk-icon-trash"></i> Ta bort medlem</button> : ""}

					<button className="uk-button uk-button-success uk-float-right" onClick={this.save}><i className="uk-icon-save"></i> Spara personuppgifter</button>
				</div>
			</form>
			</div>
		);
	},

	changeCountry: function(country)
	{
		this.getModel().set({
			address_country: country
		});
	}
});

var MemberAddHandler = React.createClass({
	getInitialState: function()
	{
		return {
			model: new MemberModel(),
		};
	},

	render: function()
	{
		return (
			<div>
				<h2>Skapa medlem</h2>
				<MemberForm model={this.state.model} />
			</div>
		);
	},
});
MemberAddHandler.title = "Skapa medlem";

module.exports = {
	MemberHandler,
	MemberAddHandler
}