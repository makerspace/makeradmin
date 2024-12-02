// TODO: it updates... just doesn't rerender ????

import React, { useEffect, useState } from "react";
import Select from "react-select";
import * as _ from "underscore";
import CollectionTable from "../Components/CollectionTable";
import Collection from "../Models/Collection";
import Permission from "../Models/Permission";
import { get } from "../gateway";

const Row = (collection) => (props) => {
    const { item } = props;
    return (
        <tr>
            <td>{item.permission}</td>
            <td>
                <a
                    onClick={() => {
                        collection.remove(item);
                    }}
                    className="removebutton"
                >
                    <i className="uk-icon-trash" />
                </a>
            </td>
        </tr>
    );
};

const GroupBoxPermissions = (props) => {
    const [showOptions, setShowOptions] = useState([]);
    const [selectedOption, setSelectedOption] = useState(null);
    const [options, setOptions] = useState([]);

    const collection = new Collection({
        type: Permission,
        url: `/membership/group/${props.match.params.group_id}/permissions`,
        idListName: "permissions",
        pageSize: 0,
    });

    useEffect(() => {
        get({ url: "/membership/permission" }).then((data) => {
            const fetchedOptions = data.data;
            setOptions(fetchedOptions);
            setShowOptions(filterOptions(fetchedOptions));
        });

        const unsubscribe = collection.subscribe(() => {
            setShowOptions(filterOptions(options));
        });

        return () => {
            unsubscribe();
        };
    }, []);

    const filterOptions = (allOptions) => {
        const existing = new Set((collection.items || []).map((i) => i.id));
        return allOptions.filter(
            (permission) => !existing.has(permission.permission_id),
        );
    };

    const selectOption = (permission) => {
        setSelectedOption(permission);

        if (_.isEmpty(permission)) {
            return;
        }

        collection.add(new Permission(permission)).then(() => {
            setSelectedOption(null);
            setShowOptions(filterOptions(options));
        });
    };

    const columns = [{ title: "Behörigheter" }];

    return (
        <div>
            <div className="uk-margin-top uk-form uk-form-stacked">
                <label className="uk-form-label" htmlFor="group">
                    Lägg till behörighet
                </label>
                <div className="uk-form-controls">
                    <Select
                        name="group"
                        className="uk-select"
                        tabIndex={1}
                        options={showOptions}
                        value={selectedOption}
                        getOptionValue={(p) => p.permission_id}
                        getOptionLabel={(p) => p.permission}
                        onChange={(permission) => selectOption(permission)}
                        isDisabled={!showOptions.length}
                    />
                </div>
            </div>
            <div className="uk-margin-top">
                <CollectionTable
                    emptyMessage="Gruppen har inga behörigheter"
                    rowComponent={Row(collection)}
                    collection={collection}
                    columns={columns}
                />
            </div>
        </div>
    );
};

export default GroupBoxPermissions;

// // class GroupBoxPermissions extends React.Component {
// //     constructor(props) {
// //         super(props);
// //         this.collection = new Collection({
// //             type: Permission,
// //             url: `/membership/group/${props.match.params.group_id}/permissions`,
// //             idListName: "permissions",
// //             pageSize: 0,
// //         });
// //         this.state = {
// //             showOptions: [],
// //             selectedOption: null,
// //         };
// //         this.options = [];

// //         get({ url: "/membership/permission" }).then((data) => {
// //             this.options = data.data;
// //             this.setState({ showOptions: this.filterOptions() });
// //         });
// //     }

// //     componentDidMount() {
// //         this.unsubscribe = this.collection.subscribe(() =>
// //             this.setState({ showOptions: this.filterOptions() }),
// //         );
// //     }

// //     componentWillUnmount() {
// //         this.unsubscribe();
// //     }

// //     filterOptions() {
// //         const existing = new Set(
// //             (this.collection.items || []).map((i) => i.id),
// //         );
// //         return this.options.filter(
// //             (permission) => !existing.has(permission.permission_id),
// //         );
// //     }

// //     selectOption(permission) {
// //         this.setState({ selectedOption: permission });

// //         if (_.isEmpty(permission)) {
// //             return;
// //         }

// //         this.collection
// //             .add(new Permission(permission))
// //             .then(this.setState({ selectedOption: null }));
// //     }

// //     render() {
// //         const columns = [{ title: "Behörigheter" }];

// //         const { showOptions, selectedOption } = this.state;

// //         return (
// //             <div>
// //                 <div className="uk-margin-top uk-form uk-form-stacked">
// //                     <label className="uk-form-label" htmlFor="group">
// //                         Lägg till behörighet
// //                     </label>
// //                     <div className="uk-form-controls">
// //                         <Select
// //                             name="group"
// //                             className="uk-select"
// //                             tabIndex={1}
// //                             options={showOptions}
// //                             value={selectedOption}
// //                             getOptionValue={(p) => p.permission_id}
// //                             getOptionLabel={(p) => p.permission}
// //                             onChange={(permission) =>
// //                                 this.selectOption(permission)
// //                             }
// //                             isDisabled={!showOptions.length}
// //                         />
// //                     </div>
// //                 </div>
// //                 <div className="uk-margin-top">
// //                     <CollectionTable
// //                         emptyMessage="Gruppen har inga behörigheter"
// //                         rowComponent={Row(this.collection)}
// //                         collection={this.collection}
// //                         columns={columns}
// //                     />
// //                 </div>
// //             </div>
// //         );
// //     }
// // }

// export default GroupBoxPermissions;
