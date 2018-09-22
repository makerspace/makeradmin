import React from 'react';
import MemberLogin from './MemberLogin';
import MemberView from './MemberView';
import auth from '../auth';
import { browserHistory } from 'react-router';


const logout = () => {
    auth.logout();
    browserHistory.push("/member");
};


export default class Member extends React.Component {
    constructor(props)
    {
        super(props);
        this.state = {isLoggedIn: auth.isLoggedIn()};
    }

    componentDidMount() {
        auth.onChange = isLoggedIn => this.setState({isLoggedIn});
    }
    
    render()
    {
        if (this.state.isLoggedIn) {
            return (
                <div className="uk-vertical-align uk-form-width-large uk-height-1-1" style={{marginLeft: "auto", marginRight: "auto", width: "600px"}}>
                    <div className="uk-vertical-align-middle uk-width-1-1">
                        <MemberView logout={logout}/>
                    </div>
                </div>
            );
        }
        
        return <MemberLogin/>;
    }
}
