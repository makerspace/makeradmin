import React from 'react';
import {withRouter} from 'react-router';
import auth from '../auth';


class HandleLogin extends React.Component
{
    componentDidMount() {
        auth.setToken(this.props.params.token);
        window.location.replace("/");
    }

    render() {
        return <p>Logging in...</p>;
    }
}

export default withRouter(HandleLogin);
