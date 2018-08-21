import React from 'react'
import { Link, withRouter } from 'react-router'

// Backbone
import SpanModel from '../../Models/Span'

module.exports = withRouter(React.createClass({
	getInitialState: function()
	{
		var span = new SpanModel({
			span_id: this.props.params.span_id
		});

		var _this = this;
		span.fetch({success: function()
		{
			// Since we do not use BackboneReact we have to update the view manually
			_this.forceUpdate();
		}});

		return {
			model: span,
		};
	},

	render: function()
	{
		var span_id = this.props.params.span_id;
		const member = this.state.model.get("firstname") + " " + this.state.model.get("lastname") + " (#" + this.state.model.get("member_number") + ")";
		const type = this.state.model.get("span_type");
		const startdate = this.state.model.get("startdate");
		const enddate = this.state.model.get("enddate");
		const span_source = this.state.model.get("creation_reason");
		return (
			<div>
				<h2>Span {span_id}</h2>
				<dl>
					<dt>Member:</dt><dd>{member}</dd>
					<dt>Type:</dt><dd>{type}</dd>
					<dt>Duration:</dt><dd>{startdate} - {enddate}</dd>
					<dt>Source:</dt><dd>{span_source}</dd>
				</dl>
			</div>
		);
	},
}));