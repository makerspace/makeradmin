import React from 'react';
import { withRouter } from 'react-router'

import MemberLogin from './MemberLogin'
import MemberView from './MemberView'
import auth from '../auth'
import { browserHistory } from 'react-router'

module.exports = withRouter(class Login extends React.Component
{
	componentWillMount()
	{
		auth.setToken(this.props.params.token);
		browserHistory.push("/" + this.props.location.query.redirect);
	}

	render()
	{
		return (
			<p>Logging in...</p>
		)
	}
});
