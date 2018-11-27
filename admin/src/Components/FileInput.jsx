import React from 'react'
//import classNames from 'classnames/bind'
import auth from '../auth'

module.exports = class FileInput extends React.Component
{
	constructor(props)
	{
		super(props);
		this.state = {
			progressbarVisible: false,
			progressbarWidth: 0,
			filename: "",
		};
	}

	componentDidMount()
	{
		var _this = this;
		var settings = {
			action: config.apiBasePath + this.props.action,
			allow : "*.(txt|xml|csv)",
			headers: {
				"Authorization": "Bearer " + auth.getAccessToken()
			},
			loadstart: function()
			{
				_this.setState({
					progressbarVisible: true,
					progressbarWidth: 0,
				});
			},

			progress: function(percent)
			{
				_this.setState({
					progressbarWidth: Math.ceil(percent),
				});
			},

			allcomplete: function(response, xhr)
			{
				// Show the progress bar for another seconds
				setTimeout(function()
				{
					_this.setState({
						progressbarVisible: false,
						progressbarWidth: 0,
					});
				}, 1000);

				// Fix error handling
				if(xhr.status == 201)
				{
					// Save the filename
					var result = JSON.parse(response);
					_this.setState({filename: result.data.filename});

					if(_this.props.onFile !== undefined)
					{
						_this.props.onFile(result.data.filename);
					}
				}
				else
				{
					alert("Upload failed");
				}

			}
		};

		var select = UIkit.uploadSelect($("#upload-select"), settings),
		drop = UIkit.uploadDrop($("#upload-drop"), settings);
/*
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
*/
	}

	clearUpload()
	{
		this.setState({filename: ""});
	}
/*
	onChange(event)
	{
		this.state.model.set(this.props.name, event.target.value);
	}
*/
	render()
	{
		return (
			<div>
				<div id="upload-drop" className="uk-placeholder">
					<p>
						<i className="uk-icon-cloud-upload uk-icon-medium uk-text-muted uk-margin-small-right"></i>
						{this.state.filename ?
							<span>{this.state.filename} (<a onClick={this.clearUpload.bind(this)}>Ta bort</a>)</span>
						:
							<span>Ladda upp genom att dra och släppa en fil här eller klicka på <a className="uk-form-file">ladda upp<input id="upload-select" className="uk-hidden" type="file" /></a>.</span>
						}
					</p>

					{this.state.progressbarVisible ?
						<div>
							<div id="progressbar" className="uk-progress">
								<div className="uk-progress-bar" style={{width: this.state.progressbarWidth + "%"}}>{this.state.progressbarWidth}%</div>
							</div>
						</div>
					: ""}
				</div>
			</div>
		);
/*
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
*/
	}
}