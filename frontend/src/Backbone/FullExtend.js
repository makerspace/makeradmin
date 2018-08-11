import Backbone from 'backbone'
import PageableCollection from 'backbone.paginator'
import auth from '../auth'
import _ from 'underscore'

// Update the Backbone sync() method to work with our RESTful API with OAuth 2.0 authentication
var backboneSync = Backbone.sync;
Backbone.sync = function(method, model, options)
{
	// Include the OAuth 2.0 access token
	options.headers = {
		"Authorization": "Bearer " + auth.getAccessToken()
	};

	// Base path for API access
	options.url = config.apiBasePath + (typeof model.url == "function" ? model.url(model) : model.url);

	// Add generic error handling to those models who doesn't implement own error handling
	var oldError = options.error;
	if(!options.disableErrorNotifications) {
		options.error = function(data, xhr, options)
		{
			if(data.status == 401)
			{
				UIkit.notify("<h2>Error</h2>You are unauthorized to use this API resource. This could be because one of the following reasons:<br><br>1) You have been logged out from the API<br>2) You do not have permissions to access this resource", {timeout: 0, status: "danger"});
			}
			else
			{
				UIkit.notify("<h2>Error</h2>Received an unexpected result from the server<br><br>" + data.status + " " + data.statusText + "<br><br><pre>" + data.responseText + "</pre>", {timeout: 0, status: "danger"});
			}

			// Call the old error method
			return oldError(data, xhr, options);
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
		return oldSuccess(model, response);
	}

	// Call the stored original Backbone.sync method with extra headers argument added
	return backboneSync(method, model, options);
};

Backbone.Model.fullExtend = function(protoProps, staticProps)
{
	if(typeof protoProps === "undefined")
	{
		var protoProps = [];
	}

	// The state of attributes at last sync
	protoProps["syncedAttributes"] = [];

	// Attributes that should not affect the isDirty function
	protoProps["ignoreAttributes"] = [];

	// Preprocess the data received from the API
	protoProps["parse"] = function(response, options)
	{
		// Do not process when a collection is updating a model
		if(options.hasOwnProperty("collection"))
		{
			return response;
		}

		return response.data;
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

			// The attribute should not affect the dirty flag
			// Very useful in dropdowns, etc
			if(this.ignoreAttributes.indexOf(key) !== -1)
			{
				continue;
			}

			// The attribute should not be in the ignorelist and it should have changed
			if(this.attributeHasChanged(key))
			{
				return true;
			}
		};
		return false;
	}

	// Return true if the specified attribute have changed since last sync
	protoProps["attributeHasChanged"] = function(name)
	{
		// A new model have changed:
		//  * There is nothing in syncedAttributes
		//  * There is a value in the form
		//  * The attribute is not the same as default value
		if(!this.syncedAttributes.hasOwnProperty(name) && this.attributes[name].length > 0 && this.attributes[name] != this.defaults[name])
		{
			return true;
		}
		// An existing model have changed:
		//  * There is data in syncedAttributes
		//  * The new value is not the same as value from last sync
		//  * 
		else if(this.syncedAttributes.hasOwnProperty(name) && this.syncedAttributes[name] != this.attributes[name])
		{
			// This is okay since we cast null to "", se Model.set() override below
			if(this.syncedAttributes[name] == null && this.attributes[name] === "")
			{
				return false;
			}
			return true;
		}

		return false;
	}

	// Make sure all null's are changed to empty strings, because otherwise React will be whining when using those values in a <input value={...} />
	// TODO: Override the set() method so when React inputs a "" it is casted to NULL
	// TODO: Make BackboneReact handle null's
	protoProps["set"] = function(attributes, options)
	{
		// Attributes is an object with multiple attributes
		if(typeof attributes === "object")
		{
			for(var key in attributes)
			{
				if(attributes[key] === null)
				{
					attributes[key] =  "";
				}
			}
		}
		// Attributes is a key and the value is in options
		else
		{
			if(options === null)
			{
				options =  "";
			}
		}

		return Backbone.Model.prototype.set.call(this, attributes, options);
	}

	// Override save so we can cast "" to null
	protoProps["save"] = function(attrs, options)
	{
		options || (options = {});
		attrs || (attrs = _.clone(this.attributes));

		// Filter the data to send to the server
		for(var key in attrs)
		{
			if(attrs[key] == "")
			{
				attrs[key] = null;
			}
		}

		options.data        = JSON.stringify(attrs);
		options.contentType = "application/json; charset=utf-8";
		options.dataType    = "json";

		// Proxy the call to the original save function
		return Backbone.Model.prototype.save.call(this, _.clone(attrs), options);
	}

	// When destroying an entity we should not care about isDirty, so we have to make it satisfied
	protoProps["destroy"] = function(options)
	{
		// isDirty is a little whiner, so we have to make syncedAttributes and attributes the same for it to shut up when leaving the page after destroying the entity.
		this.syncedAttributes = this.attributes;

		// Call the old destroy function
		return Backbone.Model.prototype.destroy.call(this, options);
	}

	// Call default extend method
	return Backbone.Model.extend.call(this, protoProps, staticProps);;
};

module.exports = Backbone