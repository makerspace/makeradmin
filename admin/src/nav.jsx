import React from "react";
import * as _ from "underscore";
import { withRouter, matchPath } from "react-router";
import { Link, NavLink } from "react-router-dom";

export const NavItem = withRouter((props) => {
    const { location, icon, to } = props;

    return (
        <li className={location.pathname.indexOf(to) >= 0 ? "uk-active" : ""}>
            <NavLink to={to}>
                {icon ? (
                    <>
                        <i className={"uk-icon-" + icon} />
                        &nbsp;
                    </>
                ) : null}
                <span>{props.children}</span>
            </NavLink>
        </li>
    );
});

export const Nav = ({ nav: { brand, items } }) => (
    <nav className="uk-navbar">
        <div className="uk-container uk-container-center">
            <Link to="/" className="uk-navbar-brand">
                {brand}
            </Link>
            <ul className="uk-navbar-nav uk-navbar-attached">
                {items.map((item, i) => (
                    <NavItem to={item.target} icon={item.icon} key={i}>
                        {item.text}
                    </NavItem>
                ))}
            </ul>
        </div>
    </nav>
);

export const SideNav = withRouter(({ nav, location }) => {
    let activeItem = _.find(
        nav.items,
        (i) => matchPath(location.pathname, i.target) !== null,
    );

    if (!activeItem || _.isUndefined(activeItem.children)) {
        return null;
    }

    return (
        <div
            className="uk-panel uk-panel-box"
            style={{ marginBottom: "1em" }}
            data-uk-sticky="{top:35}"
        >
            <ul
                className="uk-nav uk-nav-side"
                data-uk-scrollspy-nav="{closest:'li', smoothscroll:true}"
            >
                <li className="uk-nav-header">{activeItem.text}</li>
                <li className="uk-nav-divider" />
                {activeItem.children.map((item, i) => {
                    if (item.type === "separator") {
                        return <li key={i} className="uk-nav-divider" />;
                    }

                    if (item.type === "heading") {
                        return (
                            <li key={i} className="uk-nav-header">
                                {item.text}
                            </li>
                        );
                    }

                    return (
                        <NavItem
                            key={i}
                            to={item.target}
                            icon={item.icon}
                            activeItem={activeItem}
                        >
                            {item.text}
                        </NavItem>
                    );
                })}
            </ul>
        </div>
    );
});
