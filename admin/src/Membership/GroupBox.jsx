import Group from "../Models/Group";
import { NavItem } from "../nav";
import PropTypes from "prop-types";
import { withRouter } from "react-router";
import React from "react";
class GroupBox extends React.Component {
    constructor(props) {
        super(props);
        const { group_id } = props.match.params;
        this.group = Group.get(group_id);
        this.state = { group_id, title: "" };
    }

    getChildContext() {
        return { group: this.group };
    }

    componentDidMount() {
        const group = this.group;
        this.unsubscribe = group.subscribe(() =>
            this.setState({ title: group.title }),
        );
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    render() {
        const { group_id } = this.props.match.params;
        const { title } = this.state;

        return (
            <div>
                <h2>Grupp {title}</h2>

                <ul className="uk-tab">
                    <NavItem
                        icon={null}
                        to={"/membership/groups/" + group_id + "/info"}
                    >
                        Information
                    </NavItem>
                    <NavItem
                        icon={null}
                        to={"/membership/groups/" + group_id + "/members"}
                    >
                        Medlemmar
                    </NavItem>
                    <NavItem
                        icon={null}
                        to={"/membership/groups/" + group_id + "/permissions"}
                    >
                        Behörigheter
                    </NavItem>
                </ul>
                {this.props.children}
            </div>
        );
    }
}

GroupBox.childContextTypes = {
    group: PropTypes.instanceOf(Group),
};

export default withRouter(GroupBox);
