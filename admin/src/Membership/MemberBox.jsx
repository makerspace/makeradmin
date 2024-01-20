import Member from "../Models/Member";
import { NavItem } from "../nav";
import PropTypes from "prop-types";
import { withRouter } from "react-router";
import React from "react";
class MemberBox extends React.Component {
    constructor(props) {
        super(props);
        const { member_id } = props.match.params;
        this.member = Member.get(member_id);
        this.state = { member_id, firstname: "", lastname: "" };
    }

    getChildContext() {
        return { member: this.member };
    }

    componentDidMount() {
        const member = this.member;
        this.unsubscribe = member.subscribe(() =>
            this.setState({
                member_number: member.member_number,
                firstname: member.firstname,
                lastname: member.lastname,
            }),
        );
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    render() {
        const { member_id } = this.props.match.params;
        const { member_number, firstname, lastname } = this.state;

        return (
            <div>
                <h2>
                    Medlem #{member_number}: {firstname} {lastname}
                </h2>

                <ul className="uk-tab">
                    <NavItem
                        to={"/membership/members/" + member_id + "/key-handout"}
                    >
                        Medlemsintroduktion
                    </NavItem>
                    <NavItem
                        to={"/membership/members/" + member_id + "/member-data"}
                    >
                        Uppgifter
                    </NavItem>
                    <NavItem
                        to={"/membership/members/" + member_id + "/groups"}
                    >
                        Grupper
                    </NavItem>
                    <NavItem to={"/membership/members/" + member_id + "/keys"}>
                        Nycklar
                    </NavItem>
                    <NavItem
                        to={"/membership/members/" + member_id + "/permissions"}
                    >
                        Behörigheter
                    </NavItem>
                    <NavItem
                        to={"/membership/members/" + member_id + "/orders"}
                    >
                        Ordrar
                    </NavItem>
                    <NavItem
                        to={"/membership/members/" + member_id + "/messages"}
                    >
                        Utskick
                    </NavItem>
                    <NavItem to={"/membership/members/" + member_id + "/spans"}>
                        Perioder
                    </NavItem>
                </ul>
                {this.props.children}
            </div>
        );
    }
}

MemberBox.childContextTypes = {
    member: PropTypes.instanceOf(Member),
};

export default withRouter(MemberBox);
