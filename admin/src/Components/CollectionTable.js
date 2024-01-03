import React from "react";
import * as _ from "underscore";
import { confirmModal } from "../message";

export default class CollectionTable extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            sort: { key: null, order: "up" },
            items: null,
            page: {},
            loading: true,
        };
    }

    componentDidMount() {
        const { collection } = this.props;
        this.unsubscribe = collection.subscribe(({ page, items }) =>
            this.setState({ page, items, loading: false }),
        );
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    renderHeading(column, i) {
        const sortState = this.state.sort;
        const { collection } = this.props;

        if (column.title) {
            let title;
            if (column.sort) {
                const sortIcon = (
                    <i className={"uk-icon-angle-" + sortState.order} />
                );
                const onClick = () => {
                    const sort = {
                        key: column.sort,
                        order:
                            sortState.key === column.sort &&
                            sortState.order === "down"
                                ? "up"
                                : "down",
                    };
                    this.setState({ sort, loading: true });
                    collection.updateSort(sort);
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
    }

    renderPagination() {
        const { page } = this.state;
        const show_count = 2;
        const onPageNav = this.props.onPageNav;

        if (!page.count) {
            page.count = 1;
        }
        return (
            <ul className="uk-pagination" style={{ clear: "both" }}>
                {_.range(1, page.count + 1).map((i) => {
                    const distance = Math.abs(i - page.index);
                    if (distance === 0) {
                        return (
                            <li key={i} className="uk-active">
                                <span>{i}</span>
                            </li>
                        );
                    } else if (
                        distance <= show_count ||
                        i === 1 ||
                        i === page.count
                    ) {
                        return (
                            <li key={i}>
                                <a
                                    onClick={() => {
                                        this.setState({ loading: true });
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
                    return "";
                })}
            </ul>
        );
    }

    deleteItem(collection, item) {
        return confirmModal(item.deleteConfirmMessage())
            .then(() => item.del())
            .then(
                () => collection.fetch(),
                () => null,
            );
    }

    render() {
        const { rowComponent, columns, collection, emptyMessage, className } =
            this.props;
        const { items, loading } = this.state;

        let rows = null;
        if (items !== null) {
            rows = items.map((item, i) => (
                <React.Fragment key={i}>
                    {rowComponent({
                        item,
                        deleteItem: () => this.deleteItem(collection, item),
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

        const headers = columns.map((c, i) => this.renderHeading(c, i));
        const pagination =
            typeof this.state.page !== "undefined" && this.state.page.count > 1
                ? this.renderPagination()
                : null;

        return (
            <div className={className}>
                {pagination}
                <div style={{ position: "relative", clear: "both" }}>
                    <table
                        className={
                            "uk-table uk-table-condensed uk-table-striped uk-table-hover" +
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
                                    <i className="uk-icon-refresh uk-icon-spin" />{" "}
                                    Hämtar data...
                                </span>
                            </div>
                        </div>
                    ) : (
                        ""
                    )}
                </div>
                {pagination}
            </div>
        );
    }
}
