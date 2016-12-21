import React from 'react'

// Backbone
import MemberModel from '../../Models/Member'

import MemberForm from '../../Components/Forms/Member'

// Import functions from other modules
import GroupUserBox from '../../GroupUserBox'
import KeysUserBox from '../../../Keys/KeysUserBox'
import SubscriptionUserBox from '../../../Sales/SubscriptionUserBox'
import TransactionUserBox from '../../../Economy/TransactionUserBox'
import MessagesUserBox from '../../../Messages/UserBox'

module.exports = React.createClass({
	getInitialState: function()
	{
		var member = new MemberModel({
			member_id: this.props.params.id
		});

		var _this = this;
		member.fetch({
			success: function() {
				// This component does not use the ReactBackbone mixin, so we have to force redraw it when the Backbone model is loaded from the server
				// TODO: Is this one still needed? Seems to work in other components
				_this.forceUpdate();
			}
		});

//		this.title = "Meep";
		return {
			model: member,
		};
	},

	componentDidMount: function()
	{
		// Ugly way to get the switcher javascript working
		$.UIkit.init();
/*
		var _this = this;
		$("[data-uk-switcher]").on("show.uk.switcher", function(event, area)
		{
			if(area.context.id == "member_keys")
			{
				if(!this.keys_synced)
				{
					// Get the RFID keys associated with the member
					_this.state.model.keys = 
					_this.state.collection = _this.state.model.keys;

					_this.state.model.keys.fetch();
					this.keys_synced = true;
				}
			}
		});
*/
	},

	render: function()
	{
		return (
			<div>
				<h2>Medlem #{this.state.model.get("member_number")}: {this.state.model.get("firstname")} {this.state.model.get("lastname")}</h2>

				<ul className="uk-tab" data-uk-switcher="{connect:'#user-tabs'}">
					<li id="member_info"><a>Personuppgifter</a></li>
					<li id="member_groups"><a>Grupper</a></li>
					<li id="member_keys"><a>Nycklar</a></li>
					<li id="member_labaccess"><a>Prenumerationer</a></li>
					<li id="member_transactions"><a>Transaktioner</a></li>
					<li id="member_groups"><a>Utskick</a></li>
				</ul>

				<ul id="user-tabs" className="uk-switcher">
					<li>
						<MemberForm model={this.state.model} />
					</li>
					<li>
						<GroupUserBox member_id={this.state.model.get("member_id")} />
					</li>
					<li>
						KeysUserBox member_id={this.state.model.get("member_id")} /
					</li>
					<li>
						SubscriptionUserBox member_id={this.state.model.get("member_id")} /
					</li>
					<li>
						TransactionUserBox member_id={this.state.model.get("member_id")} /
					</li>
					<li>
						<MessagesUserBox member_id={this.state.model.get("member_id")} />
					</li>
				</ul>
			</div>
		);
	},
});
//MemberHandler.title = "Visa medlem";