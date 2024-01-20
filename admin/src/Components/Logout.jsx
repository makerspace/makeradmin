import auth from "../auth";
import { browserHistory } from "../browser_history";
import React from "react";

export default class Logout extends React.Component {
    componentDidMount() {
        auth.logout();
        browserHistory.push("/");
    }

    render() {
        return <p>You are now logged out</p>;
    }
}
