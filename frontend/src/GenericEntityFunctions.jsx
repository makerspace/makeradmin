import React from 'react';

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
		let _this = this;

		// User should get a warning if trying to leave the page when there is any unsaved data in the form
		this.props.router.setRouteLeaveHook(this.props.route, () =>
		{
			// TODO: När den här funktionen väl är registrerad verkar den ligga kvar tills nästa sidladdning,
			// så om modellen försvinner kommer den gnälla. En bättre lösning vore att avregistrera exit handlern,
			// när den inte längre behövs. Det här problemet dyker upp lite överallt.
			// TODO: Verkar vara fixat nu?
			if (this.state.ignoreExitHook !== true && /*this.wrapper !== undefined && this.getModel() !== undefined &&*/ this.getModel().isDirty())
			{
				return "Du har information som inte är sparad. Är du säker på att du vill lämna sidan?";
			}
			return null;
		});

		// If we create a enableSendButton() function it will be called everytime a model have changed
		// The enableSendButton() function should be used to validate the model and enable/disable the send/save button
		this.getModel().on("change sync", function() {
			_this.updateSendButton();
		});
	},

	updateSendButton: function()
	{
		if(this.hasOwnProperty("enableSendButton"))
		{
			var _this = this;
			// We need to have a delay so setState() has propely updated the state
			setTimeout(() =>
			{
				// The user might already have leaved the page via an onCreate or onUpdate handler
				// Ignore this call if the model is destroyed
				if(_this.wrapper !== undefined && _this.getModel() !== undefined)
				{
					// Note: We invert the result because we want the function to return true to activate the button, while disabled="" works the other way
					_this.setState({disableSend: !_this.enableSendButton()});
				}
			}, 100);
		}
	},

	handleChange: function(event)
	{
		// Update the model with new value
		var target = event.target;
		var key = target.getAttribute("name");
		this.getModel().set(key, target.value);

		// When we change the value of the model we have to rerender the component
		this.forceUpdate();
	},

	// Generic cancel function
	cancel: function(entity)
	{
		this.setState({ignoreExitHook: true}, () => {
			if (this.props.hasOwnProperty("onCancel"))
			{
				this.props.onCancel(entity);
			}
			else if (this.hasOwnProperty("onCancel"))
			{
				this.onCancel(entity);
			}
        });
	},

	// Generic remove function
	removeEntity: function(event)
	{
		var _this = this;

		// Prevent the form from being submitted
		event.preventDefault();

		// Ask the user from confirmation and then try to remove
		var entity = this.getModel();
		UIkit.modal.confirm(this.removeTextMessage(entity.attributes), function()
		{
			entity.destroy({
				wait: true,
				success: function(model, response)
				{
					if(response.status == "deleted")
					{
						if(_this.props.hasOwnProperty("onRemove"))
						{
							_this.props.onRemove();
						}
						else if(_this.hasOwnProperty("onRemove"))
						{
							_this.onRemove();
						}
						else
						{
							UIkit.notify("Successfully deleted", {status: "success"});
						}
					}
					else
					{
						if(_this.props.hasOwnProperty("onRemoveError"))
						{
							_this.props.onRemoveError(_this.getModel());
						}
						else if(_this.hasOwnProperty("onRemoveError"))
						{
							_this.onRemoveError(_this.getModel());
						}
						else
						{
							UIkit.notify("Error while deleting", {timeout: 0, status: "danger"});
						}
					}
				},
				error: function()
				{
					if(_this.props.hasOwnProperty("onRemoveError"))
					{
						_this.props.onRemoveError(_this.getModel());
					}
					else if(_this.hasOwnProperty("onRemoveError"))
					{
						_this.onRemoveError(_this.getModel());
					}
					else
					{
						UIkit.notify("Error while deleting", {timeout: 0, status: "danger"});
					}
				},
			});
		});
		return false;
	},

	// Generic save function
	saveEntity: function(event)
	{
		var _this = this;

		// Clear the created_at and updated_at
		this.getModel().set("created_at", null);
		this.getModel().set("updated_at", null);

		// Prevent the form from being submitted
		event.preventDefault();

		this.getModel().save(null, {
			success: function(model, response)
			{
				if(response.status == "created")
				{
					if(_this.props.hasOwnProperty("onCreate"))
					{
						_this.props.onCreate(_this.getModel());
					}
					else if(_this.hasOwnProperty("onCreate"))
					{
						_this.onCreate(_this.getModel());
					}
					else
					{
						UIkit.notify("Successfully saved", {status: "success"});
					}
				}
				else if(response.status == "updated")
				{
					if(_this.props.hasOwnProperty("onUpdate"))
					{
						_this.props.onUpdate(_this.getModel());
					}
					else if(_this.hasOwnProperty("onUpdate"))
					{
						_this.onUpdate(_this.getModel());
					}
					else
					{
						UIkit.notify("Successfully updated", {status: "success"});
					}
				}
				else
				{
					if(_this.props.hasOwnProperty("onSaveError"))
					{
						_this.props.onSaveError(_this.getModel());
					}
					else if(_this.hasOwnProperty("onSaveError"))
					{
						_this.onSaveError(_this.getModel());
					}
					else
					{
						UIkit.notify("Error while saving", {timeout: 0, status: "danger"});
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
					if(_this.props.hasOwnProperty("onSaveError"))
					{
						_this.props.onSaveError(_this.getModel());
					}
					else if(_this.hasOwnProperty("onSaveError"))
					{
						_this.onSaveError(_this.getModel());
					}
					else
					{
						UIkit.notify("Error while saving", {timeout: 0, status: "danger"});
					}
				}
			},
		});
	},

	// Render the cancel button
	cancelButton: function()
	{
		return (
			<a className="uk-button uk-button-danger uk-float-left" onClick={this.cancel}><i className="uk-icon-close"></i> Avbryt</a>
		);
	},

	// Render the remove button
	removeButton: function(text)
	{
		if(this.getModel().id === undefined)
		{
			return;
		}

		if(text === undefined)
		{
			var text = "Spara";
		}

		return (
			<a className="uk-button uk-button-danger uk-float-left" onClick={this.removeEntity}><i className="uk-icon-trash"></i> {text}</a>
		);
	},

	// Render the save button
	saveButton: function(text)
	{
		if(text === undefined)
		{
			var text = "Spara";
		}

		return (
			<button className="uk-button uk-button-success uk-float-right" disabled={this.state.disableSend} onClick={this.saveEntity}><i className="uk-icon-save"></i> {text}</button>
		);
	},
};