import React from 'react'
import BackboneReact from 'backbone-react-component'
import GenericEntityFunctions from '../../../GenericEntityFunctions'
import { withRouter } from 'react-router'
import Input from '../../../Components/Form/Input'
import Date from '../../../Components/Form/Date'
import Textarea from '../../../Components/Form/Textarea'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, GenericEntityFunctions],

	removeTextMessage: function(key)
	{
		return "Är du säker på att du vill ta bort nyckeln \"#" + key.tagid + " " + key.title + "\"?";
	},

	onRemove: function(entity)
	{
		UIkit.notify("Successfully deleted", {status: "success"});
		this.props.router.push("/keys");
	},

	onRemoveError: function(entity)
	{
		UIkit.notify("Ett fel uppstod vid borttagning av nyckel", {timeout: 0, status: "danger"});
	},

	onCreate: function(entity)
	{
		this.props.router.push("/keys/" + entity.get("key_id"));
		UIkit.notify("Successfully created", {status: "success"});
	},

	onUpdate: function(entity)
	{
		this.props.router.push("/keys");
		UIkit.notify("Successfully updated", {status: "success"});
	},

	onSaveError: function()
	{
		UIkit.notify("Error saving key", {timeout: 0, status: "danger"});
	},

	onCancel: function(entity)
	{
		this.props.router.push("/keys");
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

	// Disable the send button if there is not enough data in the form
	enableSendButton: function()
	{
		// Validate required fields
		if(
			this.getModel().isDirty() &&
			this.state.model.tagid.length > 0
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
					<div className="uk-grid">
						<div className="uk-width-1-1">
							{this.state.model.created_at != "0000-00-00T00:00:00Z" ?
								<div className="uk-grid">
									<div className="uk-width-1-2">
										<Date model={this.getModel()} name="created_at" title="Skapad" disabled={true} />
									</div>
									<div className="uk-width-1-2">
										<Date model={this.getModel()} name="updated_at" title="Ändrad" disabled={true} />
									</div>
								</div>
							: ""}

							<Input model={this.getModel()} name="tagid" title="RFID" placeholder="Använd en RFID-läsare för att läsa av det unika numret på nyckeln" />
							<Input model={this.getModel()} name="title" title="Titel" placeholder="Det är valfritt att lägga in en beskrivning av nyckeln" />
							<Textarea model={this.getModel()} name="description" title="Beskrivning" placeholder="Det är valfritt att lägga in en beskrivning av nyckeln" />

							<div className="datebox">
								<div className="uk-form-row">
									<label className="uk-form-label" htmlFor="status">
										Status
									</label>
									<div className="uk-form-controls">
										<select ref="status" id="status" name="status" value={this.state.model.status} className="uk-form-width-large" onChange={this.handleChange} >
											<option value="active">Aktiv</option>
											<option value="inactive">Inaktiv</option>
											<option value="auto">Auto</option>
										</select>
										{this.renderErrorMsg("status")}
									</div>
								</div>

								<div className="uk-form-row">
									<div className="uk-form-controls">
										<p>
											<i className="uk-icon-info-circle" />
											{(() => {
												switch (this.state.model.status) {
													case "active":   return " En aktiv nyckel är permanent aktiv inom de datum som specificeras nedan och påverkas altså inte av eventuella betalningar.";
													case "inactive": return " En inaktiv nyckel är permanent inaktiv och går ej att använda i passersystem förän den aktiveras igen.";
													case "auto":     return " Auto-läget beräknar fram om nyckeln skall vara aktiv eller ej beroende på medlemmens eventuella betalningar.";
												}
											})()}
										</p>
									</div>
								</div>

								{this.state.model.status == "active" ?
									<div className="uk-grid">
										<div className="uk-width-1-2">
											<Date model={this.getModel()} name="startdate" title="Startdatum" icon2="calendar" />
										</div>
										<div className="uk-width-1-2">
											<Date model={this.getModel()} name="enddate" title="Slutdatum" icon2="calendar" />
										</div>
									</div>
								: ""}
							</div>

							<div className="uk-form-row uk-margin-top">
								<div className="uk-form-controls">
									{this.cancelButton()}
									{this.removeButton("Ta bort nyckel")}
									{this.saveButton("Spara nyckel")}
								</div>
							</div>
						</div>
					</div>
				</form>
			</div>
		);
	},
}));