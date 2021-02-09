import React from 'react';

export default class CollectionNavigation extends React.Component {

    constructor(props) {
        super(props);
        this.onSearch = this.onSearch.bind(this);
        this.onPageNav = this.onPageNav.bind(this);

        this.params = new URLSearchParams(this.props.location.search);
        const search_term = this.params.get('search') || '';
        const page = this.params.get('page') || 1;
        this.state = {'search': search_term, 'page': page};
    }

    onSearch(term) {
        this.setState({'search': term});
        this.collection.updateSearch(term);
        if (term === "") {
            this.params.delete("search");
        } else {
            this.params.set("search", term);
        }
        this.props.history.replace(this.props.location.pathname + "?" + this.params.toString());
    }

    onPageNav(index) {
        this.setState({'page': index});
        this.collection.updatePage(index);
        this.params.set("page", index);
        this.props.history.replace(this.props.location.pathname + "?" + this.params.toString());
    }

}