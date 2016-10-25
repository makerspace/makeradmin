import React from 'react'

var DateField = React.createClass({
	render: function()
	{
		var options = {
			year: 'numeric', month: 'numeric', day: 'numeric',
			hour12: false
		};

		var str = new Intl.DateTimeFormat('sv-SE', options).format(Date.parse(this.props.date));
		return (<span>{str}</span>);
	},
});

module.exports = DateField