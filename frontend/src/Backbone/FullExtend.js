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

	// Inject our own success method
	var _this = this;
	var oldSuccess = options.success;
	options.success = function(model, response, c)
	{
		if(model.data !== undefined)
		{
			// Save the properties fetched from the server so we can use them later to compare what properties have been changed since last sync
			_this.syncedAttributes = JSON.parse(JSON.stringify(model.data));
		}

		// Call the old success method
		oldSuccess(model, response);
	}

	// Call the stored original Backbone.sync method with extra headers argument added
	var x = backboneSync(method, model, options);
};

Backbone.Model.fullExtend = function(protoProps, staticProps)
{
	if(typeof protoProps === "undefined")
	{
		var protoProps = [];
	}

	// TODO: Override the set() method so when React inputs a "" it is casted to NULL

	// The state of attributes at last sync
	protoProps["syncedAttributes"] = [];

	// Preprocess the data received from the API
	protoProps["parse"] = function(response, options)
	{
		// Do not process when a collection is updating a model
		if(options.hasOwnProperty("collection"))
		{
			return response;
		}

		// Go through the data property
		var processedResponse = {};
		for(var key in response.data)
		{
			// Make sure all null's are changed to empty strings, because otherwise React will be whining when using those values in a <input value={...} />
			if(response.hasOwnProperty(key) && response[key] === null)
			{
				processedResponse[key] =  "";
			}
			else
			{
				processedResponse[key] = response.data[key];
			}
		}

		return processedResponse;
	};

	// A function used to check if any property have changed since last sync
	protoProps["isDirty"] = function()
	{
		for(var key in this.attributes)
		{
			// Do not compare metadata
			if(
				key == this.idAttribute ||
				key == "created_at" ||
				key == "updated_at" ||
				key == "deleted_at"
			)
			{
				continue;
			}

			// A new model have changed:
			//  * There is nothing in syncedAttributes
			//  * There is a value in the form
			//  * The attribute is not the same as default value
			if(!this.syncedAttributes.hasOwnProperty(key) && this.attributes[key].length > 0 && this.attributes[key] != this.defaults[key])
			{
				return true;
			}
			// Compare the old value with the new value, but only if there really is an old value, used when changing an existing entity
			else if(this.syncedAttributes.hasOwnProperty(key) && this.syncedAttributes[key] != this.attributes[key])
			{
				return true;
			}
		};
		return false;
	}

	// When destroying an entity we should not care about isDirty, so we have to make it satisfied
	protoProps["destroy"] = function(options)
	{
		// isDirty is a little whiner, so we have to make syncedAttributes and attributes the same for it to shut up when leaving the page after destroying the entity.
		this.syncedAttributes = this.attributes;

		// Call the old destroy function
		Backbone.Model.prototype.destroy.call(this, options);
	}

	// Call default extend method
	var extended = Backbone.Model.extend.call(this, protoProps, staticProps);

	return extended;
};

module.exports = Backbone