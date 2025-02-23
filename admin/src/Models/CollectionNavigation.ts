import React from "react";
import { RouteComponentProps } from "react-router-dom";

export type CollectionNavigationProps = RouteComponentProps;
export type CollectionNavigationState = { page: number; search: string };

export default class CollectionNavigation<
    P extends CollectionNavigationProps = CollectionNavigationProps,
    S extends CollectionNavigationState = CollectionNavigationState,
> extends React.Component<P, S> {
    unsubscribe: () => void = () => {};
    params: URLSearchParams;

    constructor(props: P) {
        super(props);
        this.onSearch = this.onSearch.bind(this);
        this.onPageNav = this.onPageNav.bind(this);

        this.params = new URLSearchParams(this.props.location.search);
        const search = this.params.get("search") || "";
        const page = Number(this.params.get("page")) || 1;
        this.state = { search, page } as S;
    }

    setHistory() {
        if (this.state.search === "") {
            this.params.delete("search");
        } else {
            this.params.set("search", this.state.search);
        }

        if (!this.state.page || this.state.page === 1) {
            this.params.delete("page");
        } else {
            this.params.set("page", this.state.page.toString());
        }

        this.props.history.replace(
            this.props.location.pathname + "?" + this.params.toString(),
        );
    }

    onSearch(term: string) {
        this.setState({ search: term }, this.setHistory);
        (this as any).collection.updateSearch(term);
    }

    onPageNav(index: number) {
        this.setState({ page: index }, this.setHistory);
        (this as any).collection.updatePage(index);
    }
}
