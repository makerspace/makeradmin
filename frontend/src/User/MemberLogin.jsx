import React from 'react';
import { withRouter } from 'react-router'
import auth from '../auth'

module.exports = withRouter(class MemberLogin extends React.Component
{
	cancel()
	{
		this.props.router.push("/");
	}

	submit(e)
	{
		e.preventDefault();

		var tag = this.refs.tag.value;

		// Error handling
		if(!tag)
		{
			UIkit.modal.alert("Du måste fylla i din E-postadress");
			return;
		}

		auth.login_via_single_use_link(tag);
	}

	render()
	{
		return (
			<div className="uk-vertical-align uk-text-center uk-height-1-1">
				<div className="uk-vertical-align-middle" style={{width: "300px"}}>
					<div className="uk-text-left">
						<form className="uk-panel uk-panel-box uk-form" onSubmit={this.submit.bind(this)}>
							<div className="uk-form-row">
								<h2>Logga in</h2>
							</div>

							<div className="uk-form-row">
								<div className="uk-form-icon">
									<i className="uk-icon-user"></i>
									<input autoFocus ref="tag" className="uk-form-large uk-form-width-large" type="text" placeholder="Email/Medlemsnummer" />
								</div>
							</div>

							<div className="uk-form-row">
								<button type="submit" className="uk-width-1-1 uk-button uk-button-primary uk-button-large"><span className="uk-icon-check" /> Logga in</button>
							</div>

							{/*<div className="uk-form-row">
								<button type="button" onClick={this.cancel.bind()} className="uk-width-1-1 uk-button uk-button-secondary uk-button-large"><span className="uk-icon-close" /> Skapa ett konto</button>
							</div>*/}
						</form>
					</div>
				</div>
			</div>
		);
	}
});
