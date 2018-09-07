import React from 'react';

import MemberForm from './Components/MemberForm';
import Member from "../Models/Member";


class MemberAdd extends React.Component {

    constructor(props) {
        super(props);
        this.state = {model: new Member()};
    }

    render() {
		return (
			<div>
				<h2>Skapa medlem</h2>
				<MemberForm model={this.state.model} route={this.props.route} />
			</div>
		);
	}
}

export default MemberAdd;
