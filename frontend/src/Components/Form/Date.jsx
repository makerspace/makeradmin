import React from 'react'
import classNames from 'classnames/bind'

module.exports = class FormInput extends React.Component
{
	constructor(props)
	{
		super(props);

		this.state = {
			selected: false,
			isDirty: false,
			value: this.dateToStr(this.props.model.get(this.props.name)),
			model: this.props.model,
			error_column: "", // TODO
			error_message: "",
		};
	}

	componentDidMount()
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
		this.state.model.on("change:" + this.props.name, function()
		{
			if(_this.state.model.changed[_this.props.name] !== undefined)
			{
				// TODO: The date is not updated if the model is changed
				var str = _this.dateToStr(_this.state.model.changed[_this.props.name]);
				// Save the data
				_this.setState({
					value: str,
					isDirty: _this.state.model.attributeHasChanged(_this.props.name),
				});
			}
		});
	}

	// Take a ISO8601 timestamp and make a readable date of it
	dateToStr(input)
	{
		var options = {
			year: 'numeric', month: 'numeric', day: 'numeric',
			hour: 'numeric', minute: 'numeric', second: 'numeric',
			hour12: false
		};

		// Parse the date
		var parsed_date = Date.parse(input);

		// If the date was parsed successfully we should update the string
		if(!isNaN(parsed_date))
		{
			var str = new Intl.DateTimeFormat("sv-SE", options).format(parsed_date);
		}
		else
		{
			str = "";
		}

		return str;
	}

	// The user have changed the text in the <input />
	onChange(event)
	{
		// Do not try to parse the value if there is none
		if(event.target.value.length == 0)
		{
			this.state.model.set(this.props.name, null);

			this.setState({
				error_column: "",
				error_message: "",
				value: "",
			});

			return;
		}

		// Parse the date
		var parsed_date = new Date(event.target.value);
		if(isNaN(parsed_date))
		{
			// Save the data in the component state and set an error message
			this.setState({
				error_column: this.props.name,
				error_message: "Otillåtet datumformat",
				value: event.target.value,
			});

			if(event.target.value == "")
			{
				this.state.model.set(this.props.name, null);
			}

			// Update dirty flag
			this.setState({
				isDirty: this.state.model.attributeHasChanged(this.props.name),
			});
		}
		else
		{
			// Creeate an ISO8601 timestamp without milliseconds
			var str = parsed_date.toISOString().split('.')[0]+"Z";

			// Save the new timestamp in the model
			this.state.model.set(this.props.name, str);

			// Update dirty flag
			this.setState({
				isDirty: this.state.model.attributeHasChanged(this.props.name),
			});

			// Save the data in the component state and clear errors
			this.setState({
				error_column: "",
				error_message: "",
				value: event.target.value,
			});
		}
	}

	onFocus()
	{
		this.setState({selected: true});
	}

	onBlur()
	{
		this.setState({selected: false});
	}

	render()
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
				<div className="uk-form-controls">
					{this.props.icon ? 
						<div className="uk-form-icon">
							<i className={"uk-icon-" + this.props.icon}></i>
							<input type="text" name={this.props.name} id={this.props.name} disabled={this.props.disabled} value={this.state.value} placeholder={this.props.placeholder ? this.props.placeholder : this.props.title} onChange={this.onChange.bind(this)} className="uk-form-width-large" onFocus={this.onFocus.bind(this)} onBlur={this.onBlur.bind(this)} />
						</div>
					:
						<input type="text" name={this.props.name} id={this.props.name} disabled={this.props.disabled} value={this.state.value} placeholder={this.props.placeholder ? this.props.placeholder : this.props.title} onChange={this.onChange.bind(this)} className="uk-form-width-large" onFocus={this.onFocus.bind(this)} onBlur={this.onBlur.bind(this)} />
					}
					{this.state.error_column == this.props.name ?
						<p className="uk-form-help-block error">{this.state.error_message}</p>
					: ""}
				</div>
			</div>
		);
	}
}