import { browserHistory } from 'react-router'

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
	 *
	 */
	requestPassword(username)
	{
		$.ajax({
			method: "POST",
			url: config.apiBasePath + "/oauth/resetpassword",
			data: {
				username,
			}
		})
	},

	setToken(token)
	{
		localStorage.token = token;
		this.onChange(true);
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
			url: config.apiBasePath + "/oauth/token",
			data: {
				grant_type: "password",
				username,
				password,
			}
		})
		.always(function(data, textStatus, xhr)
		{
			if(data.status == 401)
			{
				UIkit.modal.alert("<h2>Inloggningen misslyckades</h2>Felaktigt användarnamn eller lösenord");
			}
			else if(data.status == 429)
			{
				UIkit.modal.alert("<h2>Inloggningen misslyckades</h2>För många misslyckades inloggningar. Kontot spärrat i 60 minuter");
			}
			else if(xhr.status == 200 && data.access_token !== undefined)
			{
				localStorage.token = data.access_token;
				_this.onChange(true);
			}
			else
			{
				// TODO: Generic class for error messages?
				UIkit.modal.alert("<h2>Inloggningen misslyckades</h2>Tog emot ett oväntat svar från servern:<br><br>" + data.status + " " + data.statusText + "<br><br>" + data.responseText);
			}
		});
	},

	login_via_single_use_link(tag)
	{
		$.ajax({
			method: "POST",
			url: config.apiBasePath + "/member/send_access_token",
			data: JSON.stringify({
				user_tag: tag
			}),
			contentType: "application/json; charset=utf-8",
			dataType: "json",
		}).done((data, textStatus, xhr) => {
			UIkit.modal.alert("Ett mail har skickats till dig med en magisk inloggningslänk, använd den för att slutföra din inloggning.", {status: "success"});
		}).fail((xhr, textStatus, error) => {
			if (xhr.responseJSON.status == "ambiguous")
			{
				UIkit.modal.alert("<h2>Inloggningen misslyckades</h2>Det finns flera medlemmar som matchar '" + tag + "'. Välj något som är mer unikt, t.ex email eller medlemsnummer.");
			}
			else if (xhr.responseJSON.status == "not found")
			{
				UIkit.modal.alert("<h2>Inloggningen misslyckades</h2>Ingen medlem med det namnet, email eller medlemsnummer existerar.");
			}
			else
			{
				// TODO: Generic class for error messages?
				UIkit.modal.alert("<h2>Inloggningen misslyckades</h2>Tog emot ett oväntat svar från servern:<br><br>" + xhr.status + " " + xhr.statusText + "<br><br>" + xhr.responseText);
			}
		});
	},

	/**
	 * Send an API logout request and remove the login token
	 */
	logout()
	{
		// Tell the server to delete the access token
		$.ajax({
			method: "DELETE",
			url: config.apiBasePath + "/oauth/token/" + localStorage.token,
			headers: {
				"Authorization": "Bearer " + localStorage.token
			}
		})

		// Delete from localStorage and send user to login form
		delete localStorage.token
		this.onChange(false);
	},

	/**
	 * Callback used for login/logout
	 */
	onChange() {
	}
}
