import React from 'react'
import classNames from 'classnames/bind'
import PropTypes from 'prop-types'

module.exports = React.createClass(
{
	propTypes: {
		formrow: PropTypes.bool,
	},

	getDefaultProps: function(){
		return {
			formrow: true,
		};
	},

	getInitialState: function(){
		return {
			selected: false,
			isDirty: false,
			value: this.props.model.get(this.props.name),
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
				_this.setState({
					value: _this.state.model.changed[_this.props.name],
					isDirty: _this.state.model.attributeHasChanged(_this.props.name),
				});
			}
		});
	},

	componentDidUpdate: function(prevProps, prevState) {
		if (this.props.model != prevProps.model) {
			let model = this.props.model;
			let value = this.props.model.get(this.props.name);
			this.setState({
				model: model,
				value: value,
			});
		}
	},

	onChange: function(event)
	{
		this.state.model.set(this.props.name, event.target.value);
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
				<div className="uk-form-controls">
					{this.props.icon ? 
						<div className="uk-form-icon">
							<i className={"uk-icon-" + this.props.icon}></i>
							<input type="text" name={this.props.name} id={this.props.name} disabled={this.props.disabled} value={this.state.value} placeholder={this.props.placeholder ? this.props.placeholder : this.props.title} onChange={this.onChange} className="uk-form-width-large" onFocus={this.onFocus} onBlur={this.onBlur} />
						</div>
					:
						<input type="text" name={this.props.name} id={this.props.name} disabled={this.props.disabled} value={this.state.value} placeholder={this.props.placeholder ? this.props.placeholder : this.props.title} onChange={this.onChange} className="uk-form-width-large" onFocus={this.onFocus} onBlur={this.onBlur} />
					}
					{this.state.error_column == this.props.name ?
						<p className="uk-form-help-block error">{this.state.error_message}</p>
					: ""}
				</div>
			</div>
		);
	},
});