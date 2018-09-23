import React from 'react';

import MemberForm from '../Components/MemberForm';
import Member from "../Models/Member";
import {browserHistory} from 'react-router';


class MemberAdd extends React.Component {

    constructor(props) {
        super(props);
        this.member = new Member();
    }

    render() {
        return (
            <div>
                <h2>Skapa medlem</h2>
                <MemberForm
                    member={this.member}
                    onSave={() => this.member.save().then(() => browserHistory.replace('/membership/members/' + this.member.id))}
                />
            </div>
        );
    }
}

export default MemberAdd;
