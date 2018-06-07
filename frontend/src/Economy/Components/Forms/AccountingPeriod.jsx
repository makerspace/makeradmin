import React from 'react'
import GenericEntityFunctions from '../../../GenericEntityFunctions'

module.exports = React.createClass({
	mixins: [Backbone.React.Component.mixin, GenericEntityFunctions],

	render: function()
	{
		return (
			<div>
				<form className="uk-form uk-form-horizontal">
					<div className="uk-form-row">
						<label className="uk-form-label">Namn</label>
						<div className="uk-form-controls">
							<div className="uk-form-icon">
								<i className="uk-icon-database"></i>
								<input type="text" value={this.state.model.name} className="uk-form-width-large" onChange={this.handleChange} />
							</div>
						</div>
					</div>

					<div className="uk-form-row">
						<label className="uk-form-label">Titel</label>
						<div className="uk-form-controls">
							<div className="uk-form-icon">
								<i className="uk-icon-database"></i>
								<input type="text" value={this.state.model.title} className="uk-form-width-large" onChange={this.handleChange} />
							</div>
						</div>
					</div>

					<div className="uk-form-row">
						<label className="uk-form-label">Beskrivning</label>
						<div className="uk-form-controls">
							<div className="uk-form-icon">
								<i className="uk-icon-database"></i>
								<textarea value={this.state.model.description} className="uk-form-width-large" onChange={this.handleChange} />
							</div>
						</div>
					</div>

					<div className="uk-form-row">
						<label className="uk-form-label">Startdatum</label>
						<div className="uk-form-controls">
							<input type="text" value={this.state.model.start} className="uk-form-width-large" onChange={this.handleChange} />
						</div>
					</div>

					<div className="uk-form-row">
						<label className="uk-form-label">Slutdatum</label>
						<div className="uk-form-controls">
							<input type="text" value={this.state.model.end} className="uk-form-width-large" onChange={this.handleChange} />
						</div>
					</div>
				</form>
			</div>
		);
	},
});