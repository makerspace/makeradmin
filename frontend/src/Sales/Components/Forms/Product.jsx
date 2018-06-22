import React from 'react'
import { withRouter } from 'react-router'

import DateTimeField from '../../../Components/DateTime'

import GenericEntityFunctions from '../../../GenericEntityFunctions'

import Input from '../../../Components/Form/Input'
import Textarea from '../../../Components/Form/Textarea'

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, GenericEntityFunctions],

	removeTextMessage: function(product)
	{
		return "Är du säker på att du vill ta bort produkten \"" + product.name + "\"?";
	},

	onRemove: function(entity)
	{
		UIkit.notify("Successfully deleted", {status: "success"});
		this.props.router.push("/sales/product");
	},

	onRemoveError: function()
	{
		UIkit.notify("Ett fel uppstod vid borttagning av produkten", {timeout: 0, status: "danger"});
	},

	onCreate: function(model)
	{
		UIkit.notify("Successfully created", {status: "success"});
		this.props.router.push("/sales/product/" + model.get("member_id"));
	},

	onUpdate: function(model)
	{
		UIkit.notify("Successfully updated", {status: "success"});
	},

	onSaveError: function()
	{
		UIkit.notify("Error saving product", {timeout: 0, status: "danger"});
	},

	onCancel: function(entity)
	{
		this.props.router.push("/sales/product");
	},

	// Disable the send button if there is not enough data in the form
	enableSendButton: function()
	{
		// Validate required fields
		if(
			this.getModel().isDirty() &&
			this.state.model.name.length > 0 &&
			this.state.model.category_id > 0 &&
			this.state.model.price.length > 0
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
						<legend><i className="uk-icon-shopping-cart"></i> Produkt</legend>

						<Input    model={this.getModel()} name="name"              title="Produktnamn" />
						<Input    model={this.getModel()} name="category_id"       title="Kategori" />
						<Textarea model={this.getModel()} name="description"       title="Beskrivning" />
						<Input    model={this.getModel()} name="unit"              title="Enhet" />
						<Input    model={this.getModel()} name="price"             title="Pris (SEK)" />
						<Input    model={this.getModel()} name="smallest_multiple" title="Multipel" />
					</fieldset>

					{this.state.model.id > 0 ?
						<fieldset data-uk-margin>
							<legend><i className="uk-icon-tag"></i> Metadata</legend>

							<div className="uk-form-row">
								<label className="uk-form-label">Skapad</label>
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
						{this.removeButton("Ta bort produkt")}
						{this.saveButton("Spara")}
					</div>
				</form>
			</div>
		);
	},
}));