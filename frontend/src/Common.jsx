import React from 'react'

var Loading = React.createClass({
	render: function()
	{
		return (
			<span><i className="uk-icon-refresh uk-icon-spin"></i> Hämtar data...</span>
		);
	},
});

module.exports = {
	Loading,
}