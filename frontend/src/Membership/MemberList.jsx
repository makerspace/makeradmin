import React from 'react';
import { Link } from 'react-router';
import MemberCollection from './Collections/Member';
import TableFilterBox from '../TableFilterBox';
import Members from './Components/Tables/Members';


class MemberList extends React.Component {

    constructor(props) {
        super(props);
        this.state = this.props.filters || {};
    }
    
	render() {
		return (
			<div>
				<h2>Medlemmar</h2>

				<p className="uk-float-left">På denna sida ser du en lista på samtliga medlemmar.</p>
				<Link to="/membership/membersx/add" className="uk-button uk-button-primary uk-float-right"><i className="uk-icon-plus-circle"/> Skapa ny medlem</Link>

				<TableFilterBox onChange={(filters) => this.setState({filters})} />
				<Members type={MemberCollection} filters={this.state.filters} />
			</div>
		);
	}

}

export default MemberList;
