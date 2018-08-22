import React from 'react';
import {Link, withRouter} from 'react-router';
import MemberModel from '../../Models/Member';
import PropTypes from 'prop-types';


class Show extends React.Component {
	
	constructor(props) {
		super(props);

		let member = new MemberModel({member_id: props.params.member_id});
		this.state = {member};
		
		member.fetch({success: () => {
                // Since we do not use BackboneReact we have to update the view manually
                this.forceUpdate();
		}});
    }
	
    getChildContext() {
        return {member: this.state.member};
    }
    
	render() {
		const member_id = this.props.params.member_id;
		return (
			<div>
				<h2>Medlem #{this.state.member.get("member_number")}: {this.state.member.get("firstname")} {this.state.member.get("lastname")}</h2>

				<ul className="uk-tab">
					<li><Link to={"/membership/members/" + member_id}>Personuppgifter</Link></li>
					<li><Link to={"/membership/members/" + member_id + "/groups"}>Grupper</Link></li>
					<li><Link to={"/membership/members/" + member_id + "/keys"}>Nycklar</Link></li>
					<li><Link to={"/membership/members/" + member_id + "/permissions"}>Behörigheter</Link></li>
					<li><Link to={"/membership/members/" + member_id + "/transactions"}>Transaktioner</Link></li>
					<li><Link to={"/membership/members/" + member_id + "/messages"}>Utskick</Link></li>
				</ul>
                {this.props.children}
			</div>
		);
    }
}

Show.childContextTypes = {
    member: PropTypes.instanceOf(MemberModel)
};

export default withRouter(Show);
