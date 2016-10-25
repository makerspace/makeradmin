import { browserHistory } from 'react-router'
import config from './config'

module.exports =
{
	/**
	 * Check if the user seems to be logged in (if there is a token) and if the token is valid.
	 */
	isLoggedIn()
	{
		if(localStorage.token === undefined)
		{
			return false;
		}

		// TODO: Validate token
		var validToken = true;
		if(validToken)
		{
			return true;
		}
		else
		{
			return true;
		}
	},

	/**
	 * Return the OAuth 2.0 access token
	 */
	getAccessToken()
	{
		return localStorage.token
	},

	/**
	 * Send an API login request and save the login token
	 */
	login(username, password)
	{
		var _this = this;

		// Login with OAuth 2.0
		$.ajax({
			method: "POST",
			url: config.apiBasePath + "/oauth/access_token",
			data: {
				grant_type: "password",
				client_id: config.clientId,
				client_secret: "123", // TODO: No client secret
				username,
				password,
			}
		})
		.always(function(data, textStatus, xhr)
		{
			if(xhr.status == 401)
			{
				UIkit.modal.alert("<h2>Error</h2>Authentication failed<br>Invalid username or password");
			}
			else if(xhr.status == 200 && data.access_token !== undefined)
			{
				localStorage.token = data.access_token;
				_this.onChange(true);
			}
			else
			{
				// TODO: Generic class for error messages?
				UIkit.modal.alert("<h2>Error</h2>Received an unexpected result from the server<br><br>" + xhr.status + " " + xhr.statusText + "<br><br>" + xhr.responseText);
			}
		});
	},

	/**
	 * Send an API logout request and remove the login token
	 */
	logout()
	{
		delete localStorage.token
		this.onChange(false);
		browserHistory.push("/");

		// TODO: Send API request
	},

	/**
	 * Callback used for login/logout
	 */
	onChange() {
	}
}