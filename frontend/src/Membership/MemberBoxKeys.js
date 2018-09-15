import React from 'react';
import Collection from "../Models/Collection";
import {Link} from "react-router";
import CollectionTable from "../Components/CollectionTable";
import {del, get, post} from "../gateway";
import * as _ from "underscore";


class MemberBoxKeys extends React.Component {

    constructor(props) {
        super(props);
    }
    
    render() {
        return <h1>Keys</h1>;
    }
}

export default MemberBoxKeys;
