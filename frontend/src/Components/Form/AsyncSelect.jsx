import React from 'react'
import classNames from 'classnames/bind'
import { Async } from 'react-select';
import auth from '../../auth'

module.exports = React.createClass(
{
	getInitialState: function()
	{
		return {
			selected: false,
			isDirty: false,
			value: {value: this.props.model.get(this.props.name)},
			model: this.props.model,
			error_column: "", // TODO
			error_message: "",
		};
	},

	componentDidMount: function()
	{
		var _this = this;

		// A sync event is fired when the model is saved
		// When the model is saved the field is no longer dirty
		this.state.model.on("sync", function(event)
		{
			_this.setState({
				isDirty: _this.state.model.attributeHasChanged(_this.props.name),
			});
		});

		// Update this component when the model is changed
		this.state.model.on("change", function()
		{
			if(_this.state.model.changed[_this.props.name] !== undefined)
			{
				const newvalue = _this.state.model.changed[_this.props.name];
				if (_this.state.model.changed[_this.props.name] !== _this.state.value.value) {
					_this.setState({
						value: {label: _this.props.name + "-" + newvalue, value:newvalue},
						isDirty: _this.state.model.attributeHasChanged(_this.props.name),
					});
				} else {
					_this.setState({
						isDirty: _this.state.model.attributeHasChanged(_this.props.name),
					});
				}
			}
		});
	},

	// Disable client side filtering
	filter: function(option, filterString)
	{
		return option;
	},

	search: function(input, callback)
	{
		// Clear the search history so there is no drop down with old data when search text input is empty
		if(!input || input.length < 3)
		{
			return Promise.resolve({ options: [] });
		}

		var _this = this;
		$.ajax({
			method: "GET",
			url: this.props.dataSource,
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			},
			data: {
				search: input,
			},
		}).done(function(json) {
			setTimeout(function() {
				var autoComplete = [];

				json.data.forEach(function(element, index, array){
					autoComplete.push({
						label: _this.props.getLabel(element),
						value: _this.props.getValue ? _this.props.getValue(element) : element[_this.props.name],
					});
				});

				callback(autoComplete);
			}, 100);
		});
	},

	onChange: function(value)
	{
		this.setState({
			value: value
		}, () => {
			this.state.model.set(this.props.name, value.value ? value.value : "" );
		});
	},

	onFocus: function()
	{
		this.setState({selected: true});
	},

	onBlur: function()
	{
		this.setState({selected: false});
	},

	render: function()
	{
		var classes = classNames({
			"uk-form-row": true,
			"selected": this.state.selected,
			"changed": this.state.isDirty,
			"error": this.state.error_column == this.props.name,
		});
		classes += " " + this.props.name;

		return (
			<div className={classes}>
				<label htmlFor={this.props.name} className="uk-form-label">{this.props.title}</label>
				<div>
					<Async isMulti={false} cache={false} name={this.props.name} value={this.state.value} filterOption={this.filter} loadOptions={this.search} onChange={this.onChange} onFocus={this.onFocus} onBlur={this.onBlur} />
				</div>
			</div>
		);
	},
});