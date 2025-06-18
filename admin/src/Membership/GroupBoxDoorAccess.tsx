import GroupDoorAccess from "Models/GroupDoorAccess";
import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import Select from "react-select";
import CollectionTable from "../Components/CollectionTable";
import Icon from "../Components/icons";
import Collection from "../Models/Collection";
import { get, post } from "../gateway";

interface AccessyAsset {
    id: string;
    createdAt: string;
    updatedAt: string;
    name: string;
    description: string;
    address: object;
    images: {
        id: string;
        imageId: string;
        thumbnailId: string;
        size: number;
        width: number;
        height: number;
    }[];
    roomType: string;
    category: string;
    status: string;
}

interface AccessyAssetPublication {
    id: string;
}

interface AccessyAssetWithPublication {
    asset: AccessyAsset;
    publication: AccessyAssetPublication;
}

const GroupBoxDoorAccess = () => {
    const { group_id } = useParams<{ group_id: string }>();
    const group_id_num = Number(group_id);
    const [selectedOption, setSelectedOption] =
        useState<AccessyAssetWithPublication | null>(null);
    const [options, setOptions] = useState<AccessyAssetWithPublication[]>([]);
    const [items, setItems] = useState<GroupDoorAccess[]>([]);
    const [loading, setLoading] = useState(true);
    const filteredOptions = useMemo(() => {
        return options.filter((option) => {
            return !items.some(
                (item) =>
                    item.accessy_asset_publication_guid ===
                    option.publication.id,
            );
        });
    }, [options, items]);

    const collection = useMemo(
        () =>
            new Collection({
                type: GroupDoorAccess,
                url: `/membership/group/${group_id}/door_access_permissions`,
                idListName: "door_access_permissions",
                pageSize: 0,
            }),
        [group_id],
    );

    useEffect(() => {
        get({ url: "/accessy/assets" }).then(({ data }) => {
            setOptions(data);
            setLoading(false);
        });
    }, []);

    useEffect(() => {
        // Purely for the rendering side-effect
        const unsubscribe = collection.subscribe(({ items: newItems }) => {
            setItems(newItems);
        });

        return () => {
            unsubscribe();
        };
    }, [collection]);

    const selectOption = async (item: AccessyAssetWithPublication | null) => {
        setSelectedOption(item);

        if (item !== null) {
            let access = new GroupDoorAccess({
                group_id: group_id_num,
                accessy_asset_publication_guid: item.publication.id,
            });
            await access.save();
            setSelectedOption(null);
            await collection.fetch();
            await post({
                url: `/accessy/sync`,
                expectedDataStatus: "ok",
            });
        }
    };

    const columns = [{ title: "Tillgångar" }];

    const Row = ({ item }: { item: GroupDoorAccess }) => {
        const asset = options.find(
            (o) => o.publication.id === item.accessy_asset_publication_guid,
        );
        return (
            <tr>
                <td>
                    {asset?.asset.images.map((img) => (
                        <img
                            className="accessy-asset-img-thumbnail"
                            src={
                                config.apiBasePath +
                                `/accessy/image/${img.thumbnailId}`
                            }
                        />
                    ))}
                </td>
                <td>
                    {asset !== undefined
                        ? asset.asset.name
                        : `Unknown Asset - ${item.accessy_asset_publication_guid}`}
                </td>
                <td>
                    <a
                        onClick={async () => {
                            await item.del();
                            await collection.fetch();
                            await post({
                                url: `/accessy/sync`,
                                expectedDataStatus: "ok",
                            });
                        }}
                        className="removebutton"
                    >
                        <Icon icon="trash" />
                    </a>
                </td>
            </tr>
        );
    };

    return (
        <div>
            <div className="uk-margin-top uk-form-stacked">
                <p>
                    All members of this group will get access to the following
                    Accessy assets if they have active labaccess.
                </p>
                <label className="uk-form-label" htmlFor="asset">
                    Lägg till tillgång
                </label>
                <div className="uk-form-controls">
                    <Select<AccessyAssetWithPublication, false>
                        name="asset"
                        className="uk-width-1-1"
                        tabIndex={1}
                        options={filteredOptions}
                        value={selectedOption}
                        getOptionValue={(p) => p.publication.id}
                        getOptionLabel={(p) => p.asset.name}
                        formatOptionLabel={(p) => (
                            <div>
                                {p.asset.images.length > 0 ? (
                                    <img
                                        className="accessy-asset-img-thumbnail"
                                        src={
                                            config.apiBasePath +
                                            `/accessy/image/${
                                                p.asset.images[0]!.thumbnailId
                                            }`
                                        }
                                    />
                                ) : null}
                                <span className="uk-margin-left">
                                    {p.asset.name}
                                </span>
                            </div>
                        )}
                        onChange={(p) => selectOption(p)}
                        isDisabled={!filteredOptions.length}
                        placeholder={
                            !loading && options.length == 0
                                ? "Inga Accessy-tillgångar hittades"
                                : "Välj tillgång"
                        }
                    />
                </div>
            </div>
            <div className="uk-margin-top">
                <CollectionTable
                    emptyMessage="Gruppen ger inga extra rättigheter att öppna dörrar"
                    rowComponent={Row}
                    loading={loading}
                    collection={collection}
                    columns={columns}
                />
            </div>
        </div>
    );
};

export default GroupBoxDoorAccess;
