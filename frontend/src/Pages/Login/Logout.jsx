import React from 'react';
import { browserHistory } from 'react-router'
import auth from '../../auth'

module.exports = React.createClass({
	componentDidMount() {
		auth.logout();
		browserHistory.push("/");
	},

	render() {
		return <p>You are now logged out</p>
	}
})