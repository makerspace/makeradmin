import React from 'react';
import { Link } from 'react-router';
import MemberCollection from './Collections/Member';
import Members from './Components/Tables/Members';


class SearchBox extends React.Component {
    
    constructor(props) {
        super(props);
    }
    
	render() {
		return (
			<div className="filterbox">
				<div className="uk-grid">
					<div className="uk-width-2-3">
						<form className="uk-form">
							<div className="uk-form-icon">
								<i className="uk-icon-search"/>
								<input ref="search" type="text" className="uk-form-width-large" placeholder="Skriv in ett sökord" onChange={() => this.props.onChange({search: this.refs.search.value})} />
							</div>
						</form>
					</div>
				</div>
			</div>
		);
	}
}


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

				<SearchBox onChange={(filters) => this.setState({filters})} />
				<Members type={MemberCollection} filters={this.state.filters} />
			</div>
		);
	}

}

export default MemberList;
