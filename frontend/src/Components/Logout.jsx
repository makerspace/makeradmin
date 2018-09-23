import React from 'react';
import { browserHistory } from 'react-router';
import auth from '../auth';

export default class Logout extends React.Component {
    
    componentDidMount() {
        auth.logout();
        browserHistory.push("/");
    }
    
    render() {
        return <p>You are now logged out</p>;
    }
}
