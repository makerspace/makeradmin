import React from 'react'
import { withRouter } from 'react-router'

import DateTimeField from '../../../Components/DateTime'

import GenericEntityFunctions from '../../../GenericEntityFunctions'
import Input from '../../../Components/Form/Input'
import Select from '../../../Components/Form/Select'
import Textarea from '../../../Components/Form/Textarea'
import auth from '../../../auth'

var ProductActionModel = Backbone.Model.fullExtend({
	idAttribute: "id",
	urlRoot: "/webshop/product_action",
	defaults: {
		action_id: null,
		value: "",
		name: "",
	},
});

module.exports = withRouter(React.createClass({
	mixins: [Backbone.React.Component.mixin, GenericEntityFunctions],

	getInitialState: function(){
		return {
			actions: new Array(),
			availible_actions: new Map(),
			removed_actions: [],
			all_actions: null,
		};
	},

	componentDidMount: function(){
		var _this = this;
		let actions_data = [];
		let all_actions = new Map();
		const productActionsPromise = $.ajax({
			method: "GET",
			url: config.apiBasePath + "/webshop/product_action?product_id=" + this.state.model.id,
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			},
		}).done(function(json) {
			actions_data = json.data;
		});
		const allActionsPromise = $.ajax({
			method: "GET",
			url: config.apiBasePath + "/webshop/action",
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			},
		}).done(function(json) {
			json.data.forEach(function(element,index,array){
				all_actions.set(element.id, {action_id: element.id, name: element.name});
			});
		});
		$.when(productActionsPromise, allActionsPromise).then(function() {
			let actions_array = [];
			let availible_actions = new Map(all_actions);
			actions_data.forEach(function(element, index, array){
				availible_actions.delete(element.action_id);
				let action = element;
				action.name = all_actions.get(element.action_id).name;
				actions_array.push(new ProductActionModel(action));
			});
			let actions = actions_array;
			_this.setState({
				actions: actions,
				availible_actions: availible_actions,
				all_actions: all_actions,
			});
		});
	},

	updateActionsData: function(){

	},

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

	addAction: function()
	{
		this.setState((prevState) => {
			const first_available = prevState.availible_actions.entries().next();
			if (first_available.done){ return {}; }
			const first_action_id = first_available.value[0];
			let actionModel = new ProductActionModel({
				id: null,
				action_id: first_action_id,
				value: 0,
			});
			let availible_actions = new Map(prevState.availible_actions);
			availible_actions.delete(first_action_id);
			return {
				actions: [...prevState.actions, actionModel],
				availible_actions: availible_actions,
			};
		});
	},

	removeAction: function(index)
	{
		this.setState((prevState) => {
			let removed_id = prevState.actions[index].id;
			let actions = prevState.actions.filter((element,idx,array) => {return idx != index;});

			let availible_actions = new Map(prevState.all_actions);
			actions.forEach((action) => {availible_actions.delete(action.get('action_id'));});

			let newState = {
				actions: actions,
				availible_actions: availible_actions,
			};

			if (removed_id) {
				newState.removed_actions = [...prevState.removed_actions, removed_id];
			}
			return newState;
		});
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
		let _this = this;
		const getLabel = (element) => {return element.name;};
		const getValue = (element) => {return element.id;};
		const getActionLabel = function(element){return _this.state.all_actions ? _this.state.all_actions.get(element.action_id).name : "" + element.action_id;};
		const getActionValue = function(element){return element.action_id;};
		let action_options = Array.from(this.state.availible_actions.values());
		var action_contents = this.state.actions.map(function(value, index, array){
			const options = [_this.state.all_actions.get(value.get('action_id')), ...action_options];
			return (
				<div key={index} className="uk-form-row uk-grid">
				<div className="uk-width-3-6">
					<Select model={value} formrow={false} name={"action_id"} title="Åtgärd" options={options} getLabel={getActionLabel} getValue={getActionValue} />
				</div>
				<div className="uk-width-2-6">
					<Input model={value} formrow={false} name={"value"} title="Värde" />
				</div>
				<div className="uk-width-1-6">
					<a className="uk-button uk-button-danger uk-float-left" onClick={_this.removeAction.bind(_this, index)}><i className="uk-icon-trash-o"></i></a>
				</div>
				</div>
			);
		});

		return (
			<div className="meep">
				<form className="uk-form">
					<fieldset >
						<legend><i className="uk-icon-shopping-cart"></i> Produkt</legend>

						<Input    model={this.getModel()} name="name"              title="Produktnamn" />
						<Select   model={this.getModel()} name="category_id"       title="Kategori"  getLabel={getLabel} getValue={getValue} dataSource={config.apiBasePath + "/webshop/category"} />
						<Textarea model={this.getModel()} name="description"       title="Beskrivning" />
						<Input    model={this.getModel()} name="unit"              title="Enhet" />
						<Input    model={this.getModel()} name="price"             title="Pris (SEK)" />
						<Input    model={this.getModel()} name="smallest_multiple" title="Multipel" />
					</fieldset>
					<fieldset >
						<legend><i className="uk-icon-magic"></i> Åtgärder</legend>
						<div>
							{action_contents}
						</div>
						{this.state.availible_actions.size > 0 ?
							<a className="uk-button uk-button-success uk-float-left" onClick={this.addAction}><i className="uk-icon-plus"></i> Lägg till åtgärd</a>
							:
							<div></div>
						}
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
