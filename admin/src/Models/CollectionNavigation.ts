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

    override componentDidMount() {
        this.unsubscribe = (this as any).collection.subscribe(
            ({ page }: { page: { index: number; count: number } }) =>
                this.gotNewData(page),
        );
    }

    override componentWillUnmount() {
        this.unsubscribe();
    }

    gotNewData(page: { index: number; count: number }) {
        // If the returned result has fewer number of pages, keep the page within bounds
        let index = this.state.page;
        // TODO: This seems like a bug. It shouldn't use .last_page here. I don't think that field exists.
        if (index && (page as any).last_page < index) {
            this.onPageNav((page as any).last_page);
        }
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
