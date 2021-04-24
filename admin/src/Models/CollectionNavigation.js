import React from 'react';

export default class CollectionNavigation extends React.Component {

    constructor(props) {
        super(props);
        this.onSearch = this.onSearch.bind(this);
        this.onPageNav = this.onPageNav.bind(this);

        this.params = new URLSearchParams(this.props.location.search);
        const search = this.params.get('search') || '';
        const page = this.params.get('page') || 1;
        this.state = {'search': search, 'page': page};
    }

    componentDidMount() {
        this.unsubscribe = this.collection.subscribe(({page}) => this.gotNewData(page));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }

    gotNewData(page) {
        // If the returned result has fewer number of pages, keep the page within bounds
        let index = this.state.page;
        if (index && page.count < index) {
            this.onPageNav(page.count);
        }
    }

    setHistory() {
        if (this.state.search === "") {
            this.params.delete("search");
        } else {
            this.params.set("search", this.state.search);
        }

        if (this.state.page === 1) {
            this.params.delete("page");
        } else {
            this.params.set("page", this.state.page);
        }

        this.props.history.replace(this.props.location.pathname + "?" + this.params.toString());
    }

    onSearch(term) {
        this.setState({'search': term}, this.setHistory);
        this.collection.updateSearch(term);
    }

    onPageNav(index) {
        this.setState({'page': index}, this.setHistory);
        this.collection.updatePage(index);
    }

}