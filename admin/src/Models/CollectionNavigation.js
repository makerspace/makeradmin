import React, { useState, useEffect } from "react";
import { useLocation, useHistory } from "react-router-dom";

export default function CollectionNavigation({ collection }) {
    const location = useLocation();
    const history = useHistory();
    const params = new URLSearchParams(location.search);

    const [search, setSearch] = useState(params.get("search") || "");
    const [page, setPage] = useState(Number(params.get("page")) || 1);

    useEffect(() => {
        const unsubscribe = collection.subscribe(({ page }) => {
            gotNewData(page);
        });

        return () => {
            unsubscribe();
        };
    }, [collection]);

    const gotNewData = (page) => {
        // If the returned result has fewer number of pages, keep the page within bounds
        if (page.last_page < page) {
            onPageNav(page.last_page);
        }
    };

    const setHistory = () => {
        if (search === "") {
            params.delete("search");
        } else {
            params.set("search", search);
        }

        if (page === 1) {
            params.delete("page");
        } else {
            params.set("page", page);
        }

        history.replace(location.pathname + "?" + params.toString());
    };

    const onSearch = (term) => {
        setSearch(term);
        setHistory();
        collection.updateSearch(term);
    };

    const onPageNav = (index) => {
        setPage(index);
        setHistory();
        collection.updatePage(index);
    };

    return (
        <div>
            {/* Your JSX code for rendering the navigation UI */}
        </div>
    );
}
