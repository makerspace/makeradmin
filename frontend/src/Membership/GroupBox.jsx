import React from 'react';
import {Link, withRouter} from 'react-router';
import PropTypes from 'prop-types';
import Group from "../Models/Group";


class GroupBox extends React.Component {
    
    constructor(props) {
        super(props);
        const {group_id} = props.params;
        this.group = Group.get(group_id);
        this.state = {group_id, title: ""};
    }

    getChildContext() {
        return {group: this.group};
    }

    componentDidMount() {
        const group = this.group;
        this.unsubscribe = group.subscribe(() => this.setState({title: group.title}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    render() {
        const {group_id} = this.props.params;
        const {title} = this.state;
        
        return (
            <div>
                <h2>Grupp {title}</h2>

                <ul className="uk-tab">
                    <li><Link to={"/membership/groups/" + group_id + "/info"}>Information</Link></li>
                    <li><Link to={"/membership/groups/" + group_id + "/members"}>Medlemmar</Link></li>
                    <li><Link to={"/membership/groups/" + group_id + "/permissions"}>Behörigheter</Link></li>
                </ul>
                {this.props.children}
            </div>
        );
    }
}

GroupBox.childContextTypes = {
    group: PropTypes.instanceOf(Group)
};

export default withRouter(GroupBox);
