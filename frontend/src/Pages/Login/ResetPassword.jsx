import React from 'react';
import { browserHistory } from 'react-router'
import auth from '../../auth';

class LoginResetPassword extends React.Component
{
	cancel()
	{
		browserHistory.push("/");
	}

	submit(e)
	{
		e.preventDefault();

		var username = this.refs.username.value;

		// Error handling
		if(!username)
		{
			UIkit.modal.alert("Du måste fylla i din E-postadress");
			return;
		}

		auth.requestPassword(username);

		UIkit.modal.alert("Ett E-postmeddelande med information om hur du nollställer ditt lösenord har skickats till " + username);
		browserHistory.push("/");
	}

	render()
	{
		return (
			<div className="uk-vertical-align uk-text-center uk-height-1-1">
				<div className="uk-vertical-align-middle" style={{width: "300px"}}>
					<div className="uk-text-left">
						<form className="uk-panel uk-panel-box uk-form" onSubmit={this.submit.bind(this)}>
							<div className="uk-form-row">
								<h2>Glömt ditt lösenord?</h2>
							</div>

							<div className="uk-form-row">
								<p>Fyll i ditt användarnamn så skickar vi instruktioner om hur du nollställer ditt lösenord.</p>
							</div>

							<div className="uk-form-row">
								<div className="uk-form-icon">
									<i className="uk-icon-user"></i>
									<input ref="username" className="uk-form-large uk-form-width-large" type="text" placeholder="Användarnamn" />
								</div>
							</div>

							<div className="uk-form-row">
								<button type="submit" className="uk-width-1-1 uk-button uk-button-success uk-button-large"><span className="uk-icon-check" /> Skicka E-post</button>
							</div>

							<div className="uk-form-row">
								<button type="button" onClick={this.cancel.bind()} className="uk-width-1-1 uk-button uk-button-danger uk-button-large"><span className="uk-icon-close" /> Avbryt</button>
							</div>
						</form>
					</div>
				</div>
			</div>
		);
	}
}

module.exports = LoginResetPassword;