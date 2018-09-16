import React from 'react';
import {Link, withRouter} from 'react-router';
import PropTypes from 'prop-types';
import Member from "../Models/Member";


class MemberBox extends React.Component {
    
    constructor(props) {
        super(props);
        this.member = new Member({member_id: props.params.member_id});
        this.member.refresh();
        this.state = {member_id: 0, firstname: "", lastname: ""};
    }

    getChildContext() {
        return {member: this.member};
    }

    componentDidMount() {
        const member = this.member;
        this.unsubscribeMember = member.subscribe(() => this.setState({member_number: member.member_number, firstname: member.firstname, lastname: member.lastname}));
    }
    
    componentWillUnmount() {
        this.unsubscribeMember();
    }
    
    render() {
        const {member_id} = this.props.params;
        const {member_number, firstname, lastname} = this.state;
        
        return (
            <div>
                <h2>Medlem #{member_number}: {firstname} {lastname}</h2>

                <ul className="uk-tab">
                    <li><Link to={"/membership/membersx/" + member_id + "/info"}>Personuppgifter</Link></li>
                    <li><Link to={"/membership/membersx/" + member_id + "/groups"}>Grupper</Link></li>
                    <li><Link to={"/membership/membersx/" + member_id + "/keys"}>Nycklar</Link></li>
                    <li><Link to={"/membership/membersx/" + member_id + "/permissions"}>Behörigheter</Link></li>
                    <li><Link to={"/membership/membersx/" + member_id + "/orders"}>Ordrar</Link></li>
                    <li><Link to={"/membership/membersx/" + member_id + "/messages"}>Utskick</Link></li>
                </ul>
                {this.props.children}
            </div>
        );
    }
}

MemberBox.childContextTypes = {
    member: PropTypes.instanceOf(Member)
};

export default withRouter(MemberBox);
