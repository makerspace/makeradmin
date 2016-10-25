import React from 'react'

var DateTimeField = React.createClass({
	render: function()
	{
		var str = <em>Ej angivet</em>;
		if(this.props.date != "")
		{
			var options = {
				year: 'numeric', month: 'numeric', day: 'numeric',
				hour: 'numeric', minute: 'numeric', second: 'numeric',
				hour12: false
			};

			var str = new Intl.DateTimeFormat('sv-SE', options).format(Date.parse(this.props.date));
		}

		return (<span>{str}</span>);
	},
});

module.exports = DateTimeField