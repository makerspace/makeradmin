import React from 'react';
import { withRouter } from 'react-router'

import auth from '../auth'

class Login extends React.Component
{
	componentWillMount()
	{
		auth.setToken(this.props.params.token);
		window.location.replace("/" + this.props.location.query.redirect);
	}

	render()
	{
		return (
			<p>Logging in...</p>
		)
	}
}

export default withRouter(Login);