import Backbone from 'backbone'
import PageableCollection from 'backbone.paginator'
import auth from '../auth'
import config from '../config'

// Update the Backbone sync() method to work with our RESTful API with OAuth 2.0 authentication
var backboneSync = Backbone.sync;
Backbone.sync = function(method, model, options)
{
	// Include the OAuth 2.0 access token
	options.headers = {
		"Authorization": "Bearer " + auth.getAccessToken()
	};

	// Base path for API access
	options.url = config.apiBasePath + (typeof model.url == "function" ? model.url() : model.url);

	// Add generic error handling to those models who doesn't implement own error handling
	if(!options.error)
	{
		options.error = function(data, xhr, options)
		{
			if(xhr.status == 401)
			{
				UIkit.modal.alert("<h2>Error</h2>You are unauthorized to use this API resource. This could be because one of the following reasons:<br><br>1) You have been logged out from the API<br>2) You do not have permissions to access this resource");
			}
			else
			{
				UIkit.modal.alert("<h2>Error</h2>Received an unexpected result from the server<br><br>" + data.status + " " + data.statusText + "<br><br>" + data.responseText);
			}
		}
	}

	// Call the stored original Backbone.sync method with extra headers argument added
	backboneSync(method, model, options);
};

Backbone.Model.fullExtend = function(protoProps, staticProps)
{
	if(typeof protoProps === "undefined")
	{
		var protoProps = [];
	}

	// TODO: Override the set() method so when React inputs a "" it is casted to NULL

	// Preprocess the data received from the API and make sure all null's are changed to empty strings, because otherwise React will be whining when using those values in a <input value={...} />
	protoProps["parse"] = function(response, options)
	{
		for(var key in response)
		{
			if(response.hasOwnProperty(key) && response[key] === null)
			{
				response[key] = "";
			}
		}

		return response;
	};

	// Call default extend method
	var extended = Backbone.Model.extend.call(this, protoProps, staticProps);

	return extended;
};

module.exports = Backbone