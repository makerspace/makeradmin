import React from 'react'
import BackboneReact from 'backbone-react-component'
import DateTimeField from '../../Components/DateTime'

module.exports = React.createClass({
	mixins: [Backbone.React.Component.mixin],

	render: function()
	{
		this.state.model.message_type = "sms"
		return (
			<div>
				<div className="uk-panel uk-panel-box uk-margin-bottom">
					<dl>
						<dt>Skapad</dt>
						<dd><DateTimeField date={this.state.model.created_at} /></dd>

						<dt>Typ</dt>
						<dd>
							{
									this.state.model.message_type == "email" ?
										(<span><i className="uk-icon-envelope" title="E-post" /> E-post</span>)
								:
									this.state.model.message_type == "sms" ?
										(<span><i className="uk-icon-commenting" title="SMS" /> SMS</span>)
								:
									this.state.model.message_type
							}
						</dd>

						<dt>Status</dt>
						<dd>{this.state.model.status}</dd>

						<dt>Antal mottagare</dt>
						<dd>{this.state.model.num_recipients}</dd>
					</dl>
				</div>

				<div className="uk-panel uk-panel-box uk-margin-bottom">
					{
						this.state.model.message_type != "sms" ?
							<h3 className="uk-panel-title">{this.state.model.subject}</h3>
						:
							''
					}

					
					{this.state.model.body}
				</div>
			</div>
		);
	}
});