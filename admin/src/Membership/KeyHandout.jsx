import React, { useContext } from "react";
import KeyHandoutForm from "../Components/KeyHandoutForm";
import { MemberContext } from "./MemberBox";

const KeyHandout = () => {
    const member = useContext(MemberContext);
    return (
        <div className="uk-margin-top">
            <KeyHandoutForm member={member} />
        </div>
    );
};

export default KeyHandout;
