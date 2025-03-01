import React from "react";
import { matchPath, useLocation } from "react-router";
import { Link, NavLink } from "react-router-dom";
import * as _ from "underscore";
import Icon from "./Components/icons";

export const NavItem = (props) => {
    const { icon, to } = props;
    const location = useLocation();

    return (
        <li className={location.pathname.indexOf(to) >= 0 ? "uk-active" : ""}>
            <NavLink to={to}>
                {icon ? (
                    <>
                        <Icon icon={icon} />
                        &nbsp;
                    </>
                ) : null}
                <span>{props.children}</span>
            </NavLink>
        </li>
    );
};

export const Nav = ({ nav: { brand, items } }) => (
    <nav data-uk-navbar>
        <div className="uk-navbar-center" style={{ gap: "0 2em" }}>
            <Link to="/" className="uk-navbar-item uk-logo">
                {brand}
            </Link>

            {/* Using a <ul> each with a _single_ <li> sounds insane,
                    but that's apparently the way UI-kit is built */}
            {items.map((item, i) => (
                <ul className="uk-navbar-nav" key={i}>
                    <NavItem to={item.target} icon={item.icon}>
                        {item.text}
                    </NavItem>
                </ul>
            ))}
        </div>
    </nav>
);

export const SideNav = ({ nav }) => {
    const location = useLocation();
    let activeItem = _.find(
        nav.items,
        (i) => matchPath(location.pathname, i.target) !== null,
    );

    if (!activeItem || _.isUndefined(activeItem.children)) {
        return null;
    }

    return (
        <div
            className="uk-card uk-card-default uk-card-body"
            style={{ marginBottom: "1em" }}
            data-uk-sticky="media: @m"
        >
            <ul
                className="uk-nav uk-nav-default"
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
};
