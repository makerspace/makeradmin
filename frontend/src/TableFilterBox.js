import React from 'react'

var TableFilterBox = React.createClass({
	getInitialState: function()
	{
		this.filters = {};
		return {};
	},

	buildNewFilterObject: function()
	{
		var newFilter = {};

		// Filters
		for(var key in this.filters)
		{
			var value = this.filters[key];
			console.log(key + ": " + value);
			newFilter[key] = value;
		}

		// Search
		if(this.refs.search.value != "")
		{
			newFilter["search"] = this.refs.search.value;
		}

		// Debugging
		console.log(newFilter);

		this.props.onChange(newFilter);
	},

	changeFilterValue: function(event)
	{
		var target = event.target;
		var key = target.getAttribute("name");
		this.filters[key] = target.value;

		this.buildNewFilterObject();
	},

	render: function()
	{
		return (
			<div className="filterbox">
				<div className="uk-grid">
					<div className="uk-width-2-3">
						<form className="uk-form">
							<div className="uk-form-icon">
								<i className="uk-icon-search"></i>
								<input ref="search" type="text" className="uk-form-width-large" placeholder="Skriv in ett sökord" onChange={this.buildNewFilterObject} />
							</div>
						</form>
					</div>
					<div className="uk-width-1-3">
						<div className="uk-align-right2">
							<button className="uk-button uk-float-right" data-uk-toggle="{target:'#my-id'}">Visa fler filter <i className="uk-icon uk-icon-angle-down" /></button>
						</div>
					</div>
				</div>

				<div id="my-id" className="uk-hidden">
					<label htmlFor="filter_active" className="uk-form-label">
						Aktiv:
					</label>

					<select ref="filter_active" id="filter_active" name="filter_active" onChange={this.changeFilterValue}>
						<option value="yes">Ja</option>
						<option value="no">Nej</option>
						<option value="auto">Auto</option>
					</select>

					<button className="uk-button"><i className="uk-icon uk-icon-close" /> Nollställ filter</button>
				</div>
			</div>
		);
	},
});

module.exports = TableFilterBox