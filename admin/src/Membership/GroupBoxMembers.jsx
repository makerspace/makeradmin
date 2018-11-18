import React from 'react';
import {Link} from "react-router";
import {Async} from "react-select";
import Collection from "../Models/Collection";
import Member from "../Models/Member";
import CollectionTable from "../Components/CollectionTable";
import Date from "../Components/DateShow";
import { get } from "../gateway";
import * as _ from "underscore";


const Row = collection => props => {
    const {item} = props;
    return (
        <tr>
            <td><Link to={"/membership/members/" + item.id}>{item.member_number}</Link></td>
            <td>{item.firstname}</td>
            <td>{item.lastname}</td>
            <td>{item.email}</td>
            <td><Date date={item.created_at}/></td>
            <td><a onClick={() => collection.remove(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
        </tr>
    );
};


class GroupBoxMembers extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Member, url: `/membership/group/${props.params.group_id}/members`, idListName: 'members'});
        this.state = {selectedOption: null};
    }
    
    loadOptions(inputValue, callback) {
        get({url: '/membership/member', params: {search: inputValue, sort_by: "firstname", sort_order: "asc"}}).then(data => callback(data.data));
    }

    selectOption(member) {
        this.setState({selectedOption: member});
        
        if (_.isEmpty(member)) {
            return;
        }
        
        this.collection.add(new Member(member)).then(this.setState({selectedOption: null}));
    }
    
    render() {
        const columns = [
            {title: "#", sort: "member_id"},
            {title: "Förnamn", sort: "firstname"},
            {title: "Efternamn", sort: "lastname"},
            {title: "E-post", sort: "email"},
            {title: "Blev medlem", sort: "created_at"},
            {title: ""},
        ];
        
        const {selectedOption} = this.state;
        
        return (
            <div>
                <div className="uk-margin-top uk-form uk-form-stacked">
                    <label className="uk-form-label" htmlFor="member">
                        Lägg till i grupp
                    </label>
                    <div className="uk-form-controls">
                        <Async
                            name="member"
                            tabIndex={1}
                            placeholder="Type to search for member"
                            value={selectedOption}
                            getOptionValue={m => m.member_id}
                            getOptionLabel={m => "#" + m.member_number + ": " + m.firstname + " " + (m.lastname || "") + " <" + m.email + ">"}
                            loadOptions={(v, c) => this.loadOptions(v, c)}
                            onChange={member => this.selectOption(member)}
                        />
                    </div>
                </div>
                <div className="uk-margin-top">
                    <CollectionTable emptyMessage="Inga medlemmar i grupp" rowComponent={Row(this.collection)} collection={this.collection} columns={columns} />
                </div>
            </div>
        );
    }
}

export default GroupBoxMembers;
