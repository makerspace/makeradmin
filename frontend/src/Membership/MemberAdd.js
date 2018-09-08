import React from 'react';

import MemberForm from './Components/MemberForm';
import Member from "../Models/Member";
import {browserHistory} from 'react-router';


class MemberAdd extends React.Component {

    constructor(props) {
        super(props);
        this.model = new Member();
    }

    render() {
		return (
			<div>
				<h2>Skapa medlem</h2>
				<MemberForm model={this.model} onCancel={() => {
                    this.model.reset();
                    browserHistory.goBack();
				}}/>
			</div>
		);
	}
}

export default MemberAdd;