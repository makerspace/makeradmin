import React from 'react'
import PropTypes from 'prop-types';
import classNames from 'classnames/bind'
import Select from 'react-select';
import auth from '../../auth'

module.exports = React.createClass(
{
	propTypes: {
		title: PropTypes.string,
		name: PropTypes.string,
		formrow: PropTypes.bool,
		clearable: PropTypes.bool,
		searchable: PropTypes.bool,
	},
	getDefaultProps () {
		return {
			formrow: true,
			clearable: false,
			searchable: true,
		};
	},
	getInitialState: function()
	{
		let options = (typeof this.props.options !== 'undefined') ? this.props.options : [];
		let model = (typeof this.props.model !== 'undefined') ? this.props.model : false;
		let value = model ? {value: this.props.model.get(this.props.name)} : null;

		return {
			selected: false,
			isDirty: false,
			options: options,
			model: model,
			value: value,
			error_column: "", // TODO
		};
	},

	componentDidMount: function()
	{
		var _this = this;

		this.resetOptions();

		if (this.state.model) {
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
							value: {label: newvalue.toString(), value:newvalue},
							isDirty: _this.state.model.attributeHasChanged(_this.props.name),
						});
					} else {
						_this.setState({
							isDirty: _this.state.model.attributeHasChanged(_this.props.name),
						});
					}
				}
			});
		}
	},

	componentDidUpdate: function (prevProps, prevState) {
		if (this.props.options != prevProps.options){
			this.resetOptions();
		}
		if (this.props.model != prevProps.model) {
			let model = (typeof this.props.model !== 'undefined') ? this.props.model : false;
			let value = model ? {value: this.props.model.get(this.props.name)} : this.state.value;
			this.setState({
				model: model,
				value: value,
			});
		}
	},

	toOption: function(element) {
		return {
			label: this.props.getLabel(element),
			value: this.props.getValue ? this.props.getValue(element) : element.get(this.props.name),
		};
	},

	setOptionsFromArray: function(array) {
		var _this = this;
		this.setState((prevState) => {
			let options = [];
			let selectedOption;
			const currentValue = prevState.value.value;

			array.forEach(function(element, index, array){
				const option = _this.toOption(element);
				options.push(option);
				if (option.value == currentValue) {
					selectedOption = option;
				}
			});

			return selectedOption !== undefined ? {
				value: selectedOption,
				options: options,
			}:{
				options: options,
			}
		});
	},

	resetOptions: function(){
		var _this = this;
		if(typeof this.props.options !== 'undefined'){
			this.setOptionsFromArray(this.props.options);
		} else if (this.props.dataSource) {
			$.ajax({
				method: "GET",
				url: this.props.dataSource,
				headers: {
					"Authorization": "Bearer " + auth.getAccessToken()
				},
			}).done(function(json) {
				_this.setOptionsFromArray(json.data);
			});
		}
	},

	onChange: function(value)
	{
		this.setState({
			value: value
		}, () => {
			if (this.state.model) {
				this.state.model.set(this.props.name, value.value ? value.value : "" );
			}
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
			"uk-form-row": this.props.formrow,
			"selected": this.state.selected,
			"changed": this.state.isDirty,
			"error": this.state.error_column == this.props.name,
		});
		classes += " " + this.props.name;

		return (
			<div className={classes}>
				<label htmlFor={this.props.name} className="uk-form-label">{this.props.title}</label>
				<div>
					<Select 
						ref={(ref) => {this.state.selectref = ref;}}
						name={this.props.name}
						options={this.state.options}
						value={this.state.value}
						isMulti={false}
						getOptionValue={e => e.value}
						getOptionLabel={e => e.label}
						clearable={this.props.clearable}
						searchable={this.props.searchable}
						onChange={this.onChange}
						onFocus={this.onFocus}
						onBlur={this.onBlur} />
				</div>
			</div>
		);
	},
});