import React from 'react';
import { Link } from 'react-router'
import auth from '../../auth';

class Login extends React.Component
{
	login(e)
	{
		e.preventDefault();

		var username = this.refs.username.value;
		var password = this.refs.password.value;

		// Error handling
		if(!username || !password)
		{
			UIkit.modal.alert("Du måste fylla i användarnamn och lösenord");
			return;
		}

		auth.login(username, password);
	}

	render()
	{
		return (
			<div className="uk-vertical-align uk-text-center uk-height-1-1">
				<div className="uk-vertical-align-middle" style={{width: "300px"}}>
					<form className="uk-panel uk-panel-box uk-form" onSubmit={this.login.bind(this)}>
						<div className="uk-form-row">
							<h2>Logga in</h2>
						</div>

						<div className="uk-form-row">
							<div className="uk-form-icon">
								<i className="uk-icon-user"></i>
								<input ref="username" className="uk-form-large uk-form-width-large" type="text" placeholder="Användarnamn" />
							</div>
						</div>

						<div className="uk-form-row">
							<div className="uk-form-icon">
								<i className="uk-icon-lock"></i>
								<input ref="password" className="uk-form-large uk-form-width-large" type="password" placeholder="Lösenord" />
							</div>
						</div>

						<div className="uk-form-row">
							<button type="submit" className="uk-width-1-1 uk-button uk-button-primary uk-button-large">Logga in</button>
						</div>

						<div className="uk-form-row uk-text-small">
							<Link className="uk-float-right uk-link uk-link-muted" to="/resetpassword">Glömt ditt lösenord?</Link>
						</div>
					</form>
				</div>
			</div>
		);
	}
}

module.exports = Login;