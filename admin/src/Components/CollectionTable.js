import React, { useEffect, useState } from "react";
import * as _ from "underscore";
import { confirmModal } from "../message";
import Icon from "./icons";

const deleteItem = (collection, item) => {
    return confirmModal(item.deleteConfirmMessage())
        .then(() => item.del())
        .then(
            () => collection.fetch(),
            () => null,
        );
};

const Pagination = ({
    setLoading,
    onPageNav,
    page: { index: page_index, count: page_count },
}) => {
    const show_count = 2;

    if (!page_count) {
        page_count = 1;
    }

    return (
        <ul className="uk-pagination uk-flex-center uk-clear">
            {_.range(1, page_count + 1).map((i) => {
                const distance = Math.abs(i - page_index);
                if (distance === 0) {
                    return (
                        <li key={i} className="uk-active">
                            <span>{i}</span>
                        </li>
                    );
                } else if (
                    distance <= show_count ||
                    i === 1 ||
                    i === page_count
                ) {
                    return (
                        <li key={i}>
                            <a
                                onClick={() => {
                                    setLoading(true);
                                    if (onPageNav) onPageNav(i);
                                }}
                            >
                                {i}
                            </a>
                        </li>
                    );
                } else if (distance === show_count + 1) {
                    return (
                        <li key={i}>
                            <span>...</span>
                        </li>
                    );
                }
                return null;
            })}
        </ul>
    );
};

const CollectionTable = (props) => {
    const [sort, setSort] = useState({ key: null, order: "up" });
    const [items, setItems] = useState(null);
    const [page, setPage] = useState({});
    const [loading, setLoading] = useState(true);

    const {
        collection,
        rowComponent,
        columns,
        emptyMessage,
        className,
        onPageNav,
    } = props;

    useEffect(() => {
        const unsubscribe = collection.subscribe(({ page: p, items: i }) => {
            setPage(p);
            setItems(i);
            setLoading(false);
        });
        return () => {
            unsubscribe();
        };
    }, [collection]);

    const renderHeading = (column, i) => {
        const sortState = sort;

        if (column.title) {
            let title;
            if (column.sort) {
                const sortIcon = (
                    <Icon
                        icon={
                            sortState.order === "down"
                                ? "chevron-down"
                                : "chevron-up"
                        }
                    />
                );
                const onClick = () => {
                    const newSort = {
                        key: column.sort,
                        order:
                            sortState.key === column.sort &&
                            sortState.order === "down"
                                ? "up"
                                : "down",
                    };
                    setSort(newSort);
                    setLoading(true);
                    collection.updateSort(newSort);
                };
                title = (
                    <a data-sort={column.sort} onClick={onClick}>
                        {column.title}{" "}
                        {column.sort === sortState.key ? sortIcon : ""}
                    </a>
                );
            } else {
                title = column.title;
            }
            return (
                <th key={i} className={column.class}>
                    {title}
                </th>
            );
        }
        return <th key={i} />;
    };

    let rows = null;
    if (items !== null) {
        rows = items.map((item, i) => (
            <React.Fragment key={i}>
                {rowComponent({
                    item,
                    deleteItem: () => deleteItem(collection, item),
                })}
            </React.Fragment>
        ));
        if (!rows.length && emptyMessage) {
            rows = (
                <tr>
                    <td colSpan={columns.length} className="uk-text-center">
                        <em>{emptyMessage}</em>
                    </td>
                </tr>
            );
        }
    }

    const headers = columns.map((c, i) => renderHeading(c, i));
    const pagination =
        page && page.count > 1 ? (
            <Pagination
                page={page}
                onPageNav={onPageNav}
                setLoading={setLoading}
            />
        ) : null;

    return (
        <div className={className}>
            {pagination}
            <div style={{ position: "relative", clear: "both" }}>
                <table
                    className={
                        "uk-table uk-table-small uk-table-striped uk-table-hover" +
                        (loading ? " backboneTableLoading" : "")
                    }
                >
                    <thead>
                        <tr>{headers}</tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                {loading ? (
                    <div className="loadingOverlay">
                        <div className="loadingWrapper">
                            <span>
                                <div data-uk-spinner="" />
                                Hämtar data...
                            </span>
                        </div>
                    </div>
                ) : null}
            </div>
            {pagination}
        </div>
    );
};

export default CollectionTable;
