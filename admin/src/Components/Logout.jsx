import React, { useEffect } from "react";
import auth from "../auth";
import { browserHistory } from "../browser_history";

const Logout = () => {
    useEffect(() => {
        auth.logout();
        browserHistory.push("/");
    }, []);

    return <p>You are now logged out</p>;
};

export default Logout;