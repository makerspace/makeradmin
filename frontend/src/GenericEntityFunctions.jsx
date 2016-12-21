import React from 'react'

module.exports = {
	getInitialState: function()
	{
		return {
			disableSend: true,
			ignoreExitHook: false,
		};
	},

	
	componentDidMount: function()
	{

	},

	
	componentDidMount: function()
	{
		var _this = this;

		// User should get a warning if trying to leave the page when there is any unsaved data in the form
		this.props.router.setRouteLeaveHook(this.props.route, () =>
		{
			if(this.state.ignoreExitHook !== true && this.getModel().isDirty())
			{
				return "Du har information som inte är sparad. Är du säker på att du vill lämna sidan?";
			}
		})

		// If we create a enableSendButton() function it will be called everytime a model have changed
		// The enableSendButton() function should be used to validate the model and enable/disable the send/save button
		this.getModel().on("change", function() {
			if(_this.hasOwnProperty("enableSendButton"))
			{
				_this.enableSendButton();
			}
		});
	},

	removeEntity: function(event)
	{
		var _this = this;

		// Prevent the form from being submitted
		event.preventDefault();

		// Ask the user from confirmation and then try to remove
		var entity = this.getModel();
		UIkit.modal.confirm(this.removeTextMessage(entity.attributes), function() {
			entity.destroy({
				wait: true,
				success: function(model, response) {
					if(response.status == "deleted")
					{
						if(_this.hasOwnProperty("removeSuccess"))
						{
							_this.removeSuccess();
						}
					}
					else
					{
						if(_this.hasOwnProperty("removeErrorMessage"))
						{
							_this.removeErrorMessage();
						}
					}
				},
				error: function()
				{
					if(_this.hasOwnProperty("removeErrorMessage"))
					{
						_this.removeErrorMessage();
					}
				},
			});
		});
		return false;
	},

	saveEntity: function(event)
	{
		var _this = this;

		// Prevent the form from being submitted
		event.preventDefault();

		this.getModel().save([], {
			success: function(model, response)
			{
				if(response.status == "created")
				{
					if(_this.hasOwnProperty("createdSuccess"))
					{
						_this.createdSuccess(response);
					}
					
				}
				else if(response.status == "updated")
				{
					if(_this.hasOwnProperty("updatedSuccess"))
					{
						_this.updatedSuccess(response);
					}
				}
				else
				{
					if(_this.hasOwnProperty("saveError"))
					{
						_this.saveError(response);
					}
				}
			},
			error: function(model, response, options)
			{
				if(response.status == 422)
				{
					_this.setState({
						error_column:  response.responseJSON.column,
						error_message: response.responseJSON.message,
					});
				}
				else
				{
					if(_this.hasOwnProperty("saveError"))
					{
						_this.saveError(response);
					}
				}
			},
		});
	},
};