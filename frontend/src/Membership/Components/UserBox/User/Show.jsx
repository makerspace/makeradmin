import React from 'react';
import PropTypes from 'prop-types';
import MemberModel from '../../../Models/Member';
import Member from '../../Forms/Member';


export default class Show extends React.Component {
	render() {
        return (
            <div>
                <Member model={this.context.member} route={this.props.route}/>
            </div>
        );
    }
}


Show.contextTypes = {
    member: PropTypes.instanceOf(MemberModel)
};
