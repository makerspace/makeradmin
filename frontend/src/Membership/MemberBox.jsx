import React from 'react';
import {Link, withRouter} from 'react-router';
import PropTypes from 'prop-types';
import Member from "../Models/Member";


class MemberBox extends React.Component {
    
    constructor(props) {
        super(props);
        const {member_id} = props.params;
        this.member = Member.get(member_id);
        this.state = {member_id, firstname: "", lastname: ""};
    }

    getChildContext() {
        return {member: this.member};
    }

    componentDidMount() {
        const member = this.member;
        this.unsubscribe = member.subscribe(() => this.setState({member_number: member.member_number, firstname: member.firstname, lastname: member.lastname}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    render() {
        const {member_id} = this.props.params;
        const {member_number, firstname, lastname} = this.state;
        
        return (
            <div>
                <h2>Medlem #{member_number}: {firstname} {lastname}</h2>

                <ul className="uk-tab">
                    <li><Link to={"/membership/members/" + member_id + "/member-data"}>Uppgifter</Link></li>
                    <li><Link to={"/membership/members/" + member_id + "/groups"}>Grupper</Link></li>
                    <li><Link to={"/membership/members/" + member_id + "/keys"}>Nycklar</Link></li>
                    <li><Link to={"/membership/members/" + member_id + "/permissions"}>Behörigheter</Link></li>
                    <li><Link to={"/membership/members/" + member_id + "/orders"}>Ordrar</Link></li>
                    <li><Link to={"/membership/members/" + member_id + "/messages"}>Utskick</Link></li>
                    <li><Link to={"/membership/members/" + member_id + "/spans"}>Perioder</Link></li>
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
