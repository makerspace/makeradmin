import React from 'react';

import auth from '../../auth'

module.exports = React.createClass({
	componentDidMount() {
		auth.logout()
	},

	render() {
		return <p>You are now logged out</p>
	}
})