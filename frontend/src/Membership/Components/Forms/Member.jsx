import React from 'react'
import BackboneReact from 'backbone-react-component'
import { Link, withRouter } from 'react-router'

import CountryDropdown from '../../../CountryDropdown'
import DateTimeField from '../../../Components/DateTime'

import GenericEntityFunctions from '../../../GenericEntityFunctions'

import Input from '../../../Components/Form/Input'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, GenericEntityFunctions],

	removeTextMessage: function(member)
	{
		return "Är du säker på att du vill ta bort medlemmen \"#" + member.member_number + " " + member.firstname + " " + member.lastname + "\"?";
	},

	onRemove: function(entity)
	{
		UIkit.notify("Successfully deleted", {status: "success"});
		this.props.router.push("/membership/members");
	},

	onRemoveError: function()
	{
		UIkit.notify("Ett fel uppstod vid borttagning av medlem", {timeout: 0, status: "danger"});
	},

	onCreate: function(model)
	{
		UIkit.notify("Successfully created", {status: "success"});
		this.props.router.push("/membership/members/" + model.get("member_id"));
	},

	onUpdate: function(model)
	{
		UIkit.notify("Successfully updated", {status: "success"});
	},

	onSaveError: function()
	{
		UIkit.notify("Error saving member", {timeout: 0, status: "danger"});
	},

	onCancel: function(entity)
	{
		this.props.router.push("/membership/members");
	},

	changeCountry: function(country)
	{
		this.getModel().set({
			address_country: country
		});
	},

	// Disable the send button if there is not enough data in the form
	enableSendButton: function()
	{
		// Validate required fields
		if(
			this.getModel().isDirty() &&
			this.state.model.firstname.length > 0 &&
			this.state.model.email.length > 0
		)
		{
			// Enable button
			return true;
		}

		// Disable button
		return false;
	},

	render: function()
	{
		return (
			<div className="meep">
				<form className="uk-form">
					<fieldset >
						<legend><i className="uk-icon-user"></i> Personuppgifter</legend>

						<Input model={this.getModel()} name="civicregno" title="Personnummer" />
						<Input model={this.getModel()} name="firstname"  title="Förnamn" />
						<Input model={this.getModel()} name="lastname"   title="Efternamn" />
						<Input model={this.getModel()} name="email"      title="E-post" />
						<Input model={this.getModel()} name="phone"      title="Telefonnummer" />
					</fieldset>

					<fieldset data-uk-margin>
						<legend><i className="uk-icon-home"></i> Adress</legend>

						<Input model={this.getModel()} name="address_street"  title="Address" />
						<Input model={this.getModel()} name="address_extra"   title="Address extra" placeholder="Extra adressrad, t ex C/O adress" />
						<Input model={this.getModel()} name="address_zipcode" title="Postnummer" />
						<Input model={this.getModel()} name="address_city"    title="Postort" />

						<div className="uk-form-row">
							<label htmlFor="" className="uk-form-label">Land</label>
							<div className="uk-form-controls">
								<CountryDropdown country={this.state.model.address_country} onChange={this.changeCountry} />
							</div>
						</div>
					</fieldset>

					{this.state.model.member_id > 0 ?
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
						{this.cancelButton()}
						{this.removeButton("Ta bort medlem")}
						{this.saveButton("Spara personuppgifter")}
					</div>
				</form>
			</div>
		);
	},
}));