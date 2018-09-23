import React from 'react';
import Collection from "../Models/Collection";
import {Link} from "react-router";
import Group from "../Models/Group";
import CollectionTable from "../Components/CollectionTable";
import {get} from "../gateway";
import Select from "react-select";
import * as _ from "underscore";

const filterOptions = (items, options) => {
    const current = new Set(items.map(i => i.id));
    return options.filter(o => !current.has(o.group_id));
};


const updateItems = items => prevState => {
    return {
        showOptions: filterOptions(items, prevState.options),
        items,
    };
};

const updateOptions = options => prevState => {
    return {
        showOptions: filterOptions(prevState.items, options),
        options,
    };
};


class MemberBoxGroups extends React.Component {

    constructor(props) {
        super(props);
        this.collection = new Collection({type: Group, url: `/membership/member/${props.params.member_id}/groups`, idListName: 'groups', pageSize: 0});
        this.state = {
            items: [],
            options: [],
            showOptions: [],
            selectedOption: null,
        };

        get({url: '/membership/group'}).then(data => this.setState(updateOptions(data.data)));
    }

    componentDidMount() {
        this.unsubscribe = this.collection.subscribe(({items}) => this.setState(updateItems(items || [])));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    selectOption(member_id, group) {
        this.setState({selectedOption: group});
        
        if (_.isEmpty(group)) {
            return;
        }
        
        this.collection.add(new Group(group)).then(this.setState({selectedOption: null}));
    }
    
    render() {
        const {member_id} = this.props.params;
        const {selectedOption, showOptions} = this.state;
        
        return (
            <div>
                <div className="uk-margin-top uk-form uk-form-stacked">
                    <label className="uk-form-label" htmlFor="group">
                        Lägg till i grupp
                    </label>
                    <div className="uk-form-controls">
                        <Select name="group"
                                className="uk-select"
                                tabIndex={1}
                                options={showOptions}
                                value={selectedOption}
                                getOptionValue={g => g.group_id}
                                getOptionLabel={g => g.title}
                                onChange={group => this.selectOption(member_id, group)}
                        />
                    </div>
                </div>
                <div className="uk-margin-top">
                    <CollectionTable
                        emptyMessage="Inte med i några grupper"
                        collection={this.collection}
                        columns={[
                            {title: "Titel", sort: "title"},
                            {title: "Antal medlemmar"},
                            {title: ""},
                        ]}
                        rowComponent={({item}) => (
                            <tr>
                                <td><Link to={"/membership/groups/" + item.id}>{item.title}</Link></td>
                                <td>{item.num_members}</td>
                                <td><a onClick={() => this.collection.remove(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
                            </tr>
                        )}
                    />
                </div>
            </div>
        );
    }
}

export default MemberBoxGroups;
