import KeyHandoutForm from "../Components/KeyHandoutForm";
import Member from "../Models/Member";
import PropTypes from "prop-types";
import { withRouter } from "react-router";
import React from "react";
class KeyHandout extends React.Component {
    render() {
        return (
            <div className="uk-margin-top">
                <KeyHandoutForm member={this.context.member} />
            </div>
        );
    }
}

KeyHandout.contextTypes = {
    member: PropTypes.instanceOf(Member),
};

export default withRouter(KeyHandout);
