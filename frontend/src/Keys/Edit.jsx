import React from 'react'
import BackboneReact from 'backbone-react-component'

var Edit = React.createClass({
	mixins: [Backbone.React.Component.mixin],

	getInitialState: function()
	{
		return {
			error_column: "",
			error_message: "",
		};
	},

	cancel: function(event)
	{
		// Prevent the form from being submitted
		event.preventDefault();

		// Tell parent to close form
		this.props.close();
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

		// Add a relation to the member and save the model
		this.getModel().save(
			{
				relations: [
					{
						type: "member",
						member_number: this.props.member_number
					}
				],
			},
			{
				wait: true,
				success: function()
				{
					_this.getModel().trigger("destroy", _this.getModel());

					// Tell parent to save form
					// For some reason a sync event is fired a few ms after React destroys the element, so we have to wait until the sync is done.
					setTimeout(function() {
						_this.props.save.call();
					}, 10);
				},
				error: function(model, xhr, options)
				{
					if(xhr.status == 422)
					{
						_this.setState({
							error_column:  xhr.responseJSON.column,
							error_message: xhr.responseJSON.message,
						});
					}
				},
			}
		);

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

	renderErrorMsg: function(column)
	{
		if(this.state.error_column == column)
		{
			return (
				<p className="uk-form-help-block error">Error: {this.state.error_message}</p>
			);
		}
	},

	render: function()
	{
		return (
			<form className="uk-form uk-form-horizontal">
			<div className="">
				<h3>{this.state.model.entity_id ? "Redigera RFID-tagg" : "Lägg till ny RFID-tagg"}</h3>

				<div className="uk-form-row">
					<label className="uk-form-label" htmlFor="tagid">
						ID
					</label>
					<div className="uk-form-controls">
						<input type="text" id="tagid" name="tagid" placeholder="Använd en RFID-läsare för att läsa av det unika numret på nyckeln" value={this.state.model.tagid} className="uk-form-width-large" onChange={this.handleChange} />
						{this.renderErrorMsg("tagid")}
					</div>
				</div>

				<div className="uk-form-row">
					<label className="uk-form-label" htmlFor="description">
						Beskrivning
					</label>
					<div className="uk-form-controls">
						<textarea id="description" name="description" placeholder="Det är valfritt att lägga in en beskrivning av nyckeln" value={this.state.model.description} className="uk-form-width-large" onChange={this.handleChange} />
						{this.renderErrorMsg("description")}
					</div>
				</div>

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
							<i className="uk-icon uk-icon-info-circle" />
							{(() => {
								switch (this.state.model.status) {
									case "active":   return "En aktiv nyckel är permanent aktiv inom de datum som specificeras nedan och påverkas altså inte av eventuella betalningar.";
									case "inactive": return "En inaktiv nyckel är permanent inaktiv och går ej att använda i passersystem förän den aktiveras igen.";
									case "auto":     return "Auto-läget beräknar fram om nyckeln skall vara aktiv eller ej beroende på medlemmens eventuella betalningar.";
								}
							})()}
						</p>
					</div>
				</div>

				{this.state.model.status == "active" ?
					<div className="uk-form-row">
						<label className="uk-form-label" htmlFor="startdate">
							Startdatum
						</label>
						<div className="uk-form-controls">
							<div className="uk-form-icon">
								<i className="uk-icon-calendar"></i>
								<input type="text" id="startdate" name="startdate" value={this.state.model.startdate} className="uk-form-width-large" onChange={this.handleChange} />
								{this.renderErrorMsg("startdate")}
							</div>
						</div>
					</div>
				: ""}

				{this.state.model.status == "active" ?
					<div className="uk-form-row">
						<label className="uk-form-label" htmlFor="enddate">
							Slutdatum
						</label>
						<div className="uk-form-controls">
							<div className="uk-form-icon">
								<i className="uk-icon-calendar"></i>
								<input type="text" id="enddate" name="enddate" value={this.state.model.enddate} className="uk-form-width-large" onChange={this.handleChange} />
								{this.renderErrorMsg("enddate")}
							</div>
						</div>
					</div>
				: ""}

				<div className="uk-form-row">
					<div className="uk-form-controls">
						<button className="uk-button uk-button-danger uk-float-left" onClick={this.cancel}><i className="uk-icon-close"></i> Avbryt</button>

						{this.state.model.entity_id ? <button className="uk-button uk-button-danger uk-float-left" onClick={this.remove}><i className="uk-icon-trash"></i> Ta bort nyckel</button> : ""}

						<button className="uk-button uk-button-success uk-float-right" onClick={this.save}><i className="uk-icon-save"></i> Spara nyckel</button>
					</div>
				</div>
			</div>
			</form>
		);
	},
});

module.exports = Edit