import React, { useEffect } from "react";
import auth from "../auth";
import { useNavigate } from "react-router-dom";

const Logout = () => {
    const navigate = useNavigate();
    useEffect(() => {
        auth.logout();
        navigate.push("/");
    }, []);

    return <p>You are now logged out</p>;
};

export default Logout;
