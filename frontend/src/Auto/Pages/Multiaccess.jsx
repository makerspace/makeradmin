import React from 'react'
import Multiaccess from '../Components/Multiaccess'
import File from '../../Components/Form/File'

module.exports = React.createClass({
	getInitialState: function()
	{
		return {
		};
	},

	componentDidMount: function()
	{
		this.setState({
			filename: ""
		});
	},

	uploadComplete: function(filename)
	{
		this.setState({filename});
	},

	render: function()
	{
		return (
			<div>
				<h1>MultiAccess avstämning</h1>

				<File action="/multiaccess/upload" onFile={this.uploadComplete} />

				<Multiaccess filename={this.state.filename} />
			</div>
		);
	},
});