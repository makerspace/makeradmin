import React from 'react';
import { withRouter } from 'react-router'

import MemberLogin from './MemberLogin'
import MemberView from './MemberView'
import auth from '../auth'
import { browserHistory } from 'react-router'

module.exports = withRouter(class Member extends React.Component
{
	constructor(props)
	{
		super(props);
		this.state = { isLoggedIn: false };
	}

	updateAuth()
	{
		this.setState({
			isLoggedIn: auth.isLoggedIn()
		});
	}

	componentWillMount()
	{
		auth.onChange = () => this.updateAuth();
		this.updateAuth();
	}

	logout()
	{
		auth.logout();
		browserHistory.push("/member");
	}

	render()
	{
		if(this.state.isLoggedIn === true)
		{
			return (
				<div className="uk-vertical-align uk-form-width-large uk-height-1-1" style={{marginLeft: "auto", marginRight: "auto", width: "600px"}}>
					<div className="uk-vertical-align-middle uk-width-1-1">
						<MemberView logout={this.logout.bind(this)}/>
					</div>
				</div>
			);
		}
		else
		{
			return (
				<MemberLogin />
			);
		}
	}
});
